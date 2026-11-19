import re
from collections.abc import Callable, Iterator
from typing import Any, Optional
from urllib.parse import urlparse

import spotipy
from spotipy.cache_handler import CacheFileHandler
from spotipy.exceptions import SpotifyException

from .config import Credentials
from .errors import SpotifyAccessError
from .models import Playlist, Track

SCOPES = "playlist-read-private playlist-read-collaborative"

_PLAYLIST_ID = re.compile(r"^[A-Za-z0-9]{22}$")


def parse_playlist_id(value: str) -> str:
    """Extract a playlist ID from a Spotify playlist URL, ``spotify:playlist:`` URI or bare ID."""
    text = value.strip()
    candidate = ""
    if text.startswith("spotify:"):
        parts = text.split(":")
        if len(parts) >= 3 and parts[-2] == "playlist":
            candidate = parts[-1]
    elif "://" in text or text.startswith("open.spotify.com"):
        parsed = urlparse(text if "://" in text else "https://" + text)
        segments = [segment for segment in parsed.path.split("/") if segment]
        if "playlist" in segments:
            index = segments.index("playlist")
            if index + 1 < len(segments):
                candidate = segments[index + 1]
    else:
        candidate = text
    if not _PLAYLIST_ID.match(candidate):
        raise ValueError(f"Not a Spotify playlist URL, URI or ID: {value!r}")
    return candidate


def create_spotify(
    credentials: Optional[Credentials] = None,
    user: Optional[str] = None,
    auth_manager: Optional[spotipy.oauth2.SpotifyAuthBase] = None,
) -> spotipy.Spotify:
    if auth_manager is None:
        if credentials is None:
            raise ValueError("Either credentials or an auth_manager is required")
        cache_handler = CacheFileHandler(cache_path=f".cache-{user}" if user else None, username=user)
        auth_manager = spotipy.SpotifyOAuth(
            client_id=credentials.spotify_client_id,
            client_secret=credentials.spotify_client_secret,
            redirect_uri=credentials.spotify_redirect_uri,
            scope=SCOPES,
            cache_handler=cache_handler,
        )
    return spotipy.Spotify(auth_manager=auth_manager)


class SpotifyLibrary:
    """Reads the current user's playlists through a :class:`spotipy.Spotify` client."""

    def __init__(self, sp: spotipy.Spotify):
        self.sp = sp

    def playlists(self) -> list[Playlist]:
        page = self._call(None, self.sp.current_user_playlists, limit=50)
        result = []
        for item in self._paginate(page, None):
            if not item:
                continue
            contents = item.get("items") or item.get("tracks") or {}
            result.append(
                Playlist(
                    id=item["id"],
                    name=item.get("name") or "",
                    owner=(item.get("owner") or {}).get("display_name") or "",
                    total_tracks=contents.get("total") if isinstance(contents, dict) else None,
                )
            )
        return result

    def playlist_name(self, playlist_id: str) -> str:
        return self._call(playlist_id, self.sp.playlist, playlist_id, fields="name")["name"]

    def tracks(self, playlist_id: str) -> tuple[list[Track], int]:
        """Return the playlist's songs, plus how many entries were skipped.

        Local files, podcast episodes and tracks that are no longer available are skipped.
        """
        page = self._call(playlist_id, self.sp.playlist_items, playlist_id, limit=100, additional_types=("track",))
        tracks: list[Track] = []
        skipped = 0
        for entry in self._paginate(page, playlist_id):
            item = (entry or {}).get("item") or (entry or {}).get("track")
            if not item or entry.get("is_local") or item.get("is_local") or item.get("type", "track") != "track":
                skipped += 1
                continue
            artists = item.get("artists") or []
            tracks.append(
                Track(
                    name=item.get("name") or "",
                    artist=(artists[0].get("name") or "") if artists else "",
                    isrc=(item.get("external_ids") or {}).get("isrc"),
                    spotify_id=item.get("id"),
                )
            )
        return tracks, skipped

    def _paginate(self, page: Optional[dict], playlist_id: Optional[str]) -> Iterator[Any]:
        while page:
            yield from page.get("items") or []
            page = self._call(playlist_id, self.sp.next, page) if page.get("next") else None

    def _call(self, playlist_id: Optional[str], fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except SpotifyException as exc:
            if playlist_id and exc.http_status == 404:
                raise SpotifyAccessError(f"Spotify playlist {playlist_id} was not found") from exc
            if exc.http_status == 403:
                target = f"playlist {playlist_id}" if playlist_id else "your playlists"
                raise SpotifyAccessError(
                    f"Spotify refused access to {target}. Apps in development mode can only read "
                    "playlists you own or collaborate on, and your account must be on the app's user list "
                    "in the Spotify developer dashboard."
                ) from exc
            raise
