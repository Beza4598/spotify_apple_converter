import time
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import Any, Optional, TypeVar

import jwt
import requests

from .config import Credentials
from .errors import AppleMusicError

API_ROOT = "https://api.music.apple.com/v1"
ISRC_BATCH_SIZE = 25
ADD_BATCH_SIZE = 25
DEFAULT_STOREFRONT = "us"
PLAYLIST_DESCRIPTION = "Transferred from Spotify with spotify-to-apple-py."

_T = TypeVar("_T")


def _chunks(items: Sequence[_T], size: int) -> Iterator[Sequence[_T]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


class AppleMusicClient:
    """A small client for the parts of the Apple Music API this library needs.

    Rate-limited requests (HTTP 429) are retried after the delay Apple asks for.
    Server errors are retried only for read requests, so a write is never repeated
    after Apple may already have applied it.
    """

    def __init__(
        self,
        key_id: str,
        team_id: str,
        private_key: str,
        music_user_token: str,
        *,
        storefront: Optional[str] = None,
        token_lifetime: float = 12 * 3600,
        max_retries: int = 5,
        session: Optional[requests.Session] = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.key_id = key_id
        self.team_id = team_id
        self.music_user_token = music_user_token
        self.token_lifetime = token_lifetime
        self.max_retries = max_retries
        self._private_key = private_key
        self._storefront = storefront
        self._session = session or requests.Session()
        self._sleep = sleep
        self._token: Optional[str] = None
        self._token_expires = 0.0

    @classmethod
    def from_credentials(cls, credentials: Credentials, **kwargs: Any) -> "AppleMusicClient":
        return cls(
            credentials.apple_key_id or "",
            credentials.apple_team_id or "",
            credentials.apple_private_key or "",
            credentials.apple_music_user_token or "",
            **kwargs,
        )

    @property
    def developer_token(self) -> str:
        now = time.time()
        if self._token is None or now >= self._token_expires - 300:
            expires = now + self.token_lifetime
            payload = {"iss": self.team_id, "iat": int(now), "exp": int(expires)}
            self._token = jwt.encode(payload, self._private_key, algorithm="ES256", headers={"kid": self.key_id})
            self._token_expires = expires
        return self._token

    @property
    def storefront(self) -> str:
        if self._storefront is None:
            try:
                data = self._request("GET", "/me/storefront", retry_server_errors=True).json()
                self._storefront = data["data"][0]["id"]
            except AppleMusicError as exc:
                if exc.is_auth_error:
                    raise
                self._storefront = DEFAULT_STOREFRONT
            except (KeyError, IndexError, ValueError):
                self._storefront = DEFAULT_STOREFRONT
        return self._storefront

    def songs_by_isrc(self, isrcs: Iterable[str]) -> dict[str, str]:
        """Return a mapping of upper-cased ISRC to Apple Music catalog song ID."""
        wanted = list(dict.fromkeys(isrc.strip().upper() for isrc in isrcs if isrc and isrc.strip()))
        found: dict[str, str] = {}
        for chunk in _chunks(wanted, ISRC_BATCH_SIZE):
            try:
                response = self._request(
                    "GET",
                    f"/catalog/{self.storefront}/songs",
                    params={"filter[isrc]": ",".join(chunk)},
                    retry_server_errors=True,
                )
            except AppleMusicError as exc:
                if exc.status == 404:
                    continue
                raise
            body = response.json()
            by_filter = body.get("meta", {}).get("filters", {}).get("isrc", {})
            for isrc, songs in by_filter.items():
                if songs:
                    found.setdefault(isrc.upper(), songs[0]["id"])
            for song in body.get("data", []):
                isrc = (song.get("attributes", {}).get("isrc") or "").upper()
                if isrc in chunk:
                    found.setdefault(isrc, song["id"])
        return found

    def create_playlist(self, name: str, description: str = PLAYLIST_DESCRIPTION) -> str:
        """Create a playlist in the user's library and return its ID."""
        body = {"attributes": {"name": name, "description": description}}
        response = self._request("POST", "/me/library/playlists", json=body)
        return response.json()["data"][0]["id"]

    def add_tracks(self, playlist_id: str, song_ids: Sequence[str]) -> list[bool]:
        """Add catalog songs to a library playlist, in order.

        Returns one flag per song saying whether it was added. If Apple rejects a batch,
        its songs are retried one at a time so a single bad song doesn't sink the rest.
        """
        results: list[bool] = []
        for chunk in _chunks(song_ids, ADD_BATCH_SIZE):
            try:
                self._post_tracks(playlist_id, chunk)
                results.extend([True] * len(chunk))
            except AppleMusicError as exc:
                if exc.is_auth_error:
                    raise
                if exc.status >= 500 or len(chunk) == 1:
                    results.extend([False] * len(chunk))
                    continue
                for song_id in chunk:
                    results.append(self._try_post_track(playlist_id, song_id))
        return results

    def _try_post_track(self, playlist_id: str, song_id: str) -> bool:
        try:
            self._post_tracks(playlist_id, [song_id])
        except AppleMusicError as exc:
            if exc.is_auth_error:
                raise
            return False
        return True

    def _post_tracks(self, playlist_id: str, song_ids: Sequence[str]) -> None:
        body = {"data": [{"id": song_id, "type": "songs"} for song_id in song_ids]}
        self._request("POST", f"/me/library/playlists/{playlist_id}/tracks", json=body)

    def _request(
        self, method: str, path: str, *, retry_server_errors: bool = False, **kwargs: Any
    ) -> requests.Response:
        for attempt in range(self.max_retries + 1):
            headers = {
                "Authorization": f"Bearer {self.developer_token}",
                "Music-User-Token": self.music_user_token,
            }
            response = self._session.request(method, API_ROOT + path, headers=headers, timeout=30, **kwargs)
            status = response.status_code
            retryable = status == 429 or (retry_server_errors and status >= 500)
            if not retryable or attempt == self.max_retries:
                break
            self._sleep(_retry_delay(response, attempt))
        if status >= 400:
            raise AppleMusicError(status, _error_message(response))
        return response


def _retry_delay(response: requests.Response, attempt: int) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return max(float(retry_after), 0.0)
        except ValueError:
            pass
    return float(min(2**attempt, 30))


def _error_message(response: requests.Response) -> str:
    try:
        error = response.json()["errors"][0]
        message = error.get("detail") or error.get("title") or response.reason
    except (ValueError, KeyError, IndexError, TypeError):
        message = response.text[:200] or response.reason
    if response.status_code == 401:
        message += " (check APPLE_KEY_ID, APPLE_TEAM_ID and your private key)"
    elif response.status_code == 403:
        message += " (your Music User Token may be expired, or the account has no Apple Music subscription)"
    return message
