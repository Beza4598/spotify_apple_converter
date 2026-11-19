from collections.abc import Iterable
from pathlib import Path
from typing import Any, Optional, Union

import spotipy

from .apple import AppleMusicClient
from .config import Credentials
from .errors import AppleMusicError, SpotifyAccessError
from .models import Playlist, TransferResult
from .spotify import SpotifyLibrary, create_spotify, parse_playlist_id


class SpotifyClient:
    """Transfers playlists from Spotify to an Apple Music library.

    Args:
        user: Optional name used for the Spotify token cache file (``.cache-<user>``).
        path: Path to the Apple Music ``.p8`` private key. Defaults to
            ``APPLE_PRIVATE_KEY_PATH`` or ``APPLE_PRIVATE_KEY`` from the environment.
        auth_manager: A spotipy auth manager to use instead of the default OAuth flow.
        credentials: Credentials to use instead of reading them from the environment.
        storefront: Apple Music storefront code such as ``"us"`` or ``"gb"``. Detected
            from the Apple Music account when not given.
        spotify: A ready-made :class:`spotipy.Spotify` client.
        apple: A ready-made :class:`AppleMusicClient`.
        verbose: Print progress and a summary for each playlist.
    """

    def __init__(
        self,
        user: Optional[str] = None,
        path: Optional[Union[str, Path]] = None,
        auth_manager: Optional[spotipy.oauth2.SpotifyAuthBase] = None,
        *,
        credentials: Optional[Credentials] = None,
        storefront: Optional[str] = None,
        spotify: Optional[spotipy.Spotify] = None,
        apple: Optional[AppleMusicClient] = None,
        verbose: bool = True,
    ):
        needs_spotify = spotify is None and auth_manager is None
        if credentials is None and (needs_spotify or apple is None):
            credentials = Credentials.from_env(path, spotify=needs_spotify, apple=apple is None)
        self.user = user
        self.verbose = verbose
        self.spotify = SpotifyLibrary(spotify or create_spotify(credentials, user, auth_manager))
        if apple is None:
            assert credentials is not None
            apple = AppleMusicClient.from_credentials(credentials, storefront=storefront)
        self.apple = apple

    def list_playlists(self) -> list[Playlist]:
        """Return the current user's Spotify playlists."""
        return self.spotify.playlists()

    def transfer_single_playlist(
        self, playlist_url: str, playlist_name: Optional[str] = None, *, dry_run: bool = False
    ) -> TransferResult:
        """Copy one Spotify playlist into the Apple Music library.

        Args:
            playlist_url: A Spotify playlist URL, ``spotify:playlist:`` URI or playlist ID.
            playlist_name: Name for the Apple Music playlist. Defaults to the Spotify name.
            dry_run: Match the songs but don't create anything on Apple Music.

        Raises:
            ValueError: ``playlist_url`` isn't a Spotify playlist.
            SpotifyAccessError: Spotify won't return the playlist.
            AppleMusicError: Apple Music rejected the request.
        """
        playlist_id = parse_playlist_id(playlist_url)
        name = playlist_name or self.spotify.playlist_name(playlist_id)
        return self._transfer(playlist_id, name, dry_run)

    def transfer_all_playlists(
        self, playlist_ids: Optional[Iterable[str]] = None, *, dry_run: bool = False
    ) -> list[TransferResult]:
        """Copy every playlist in the user's Spotify library, or only those in ``playlist_ids``.

        A playlist Spotify won't return is recorded with an ``error`` and the rest carry on.
        Apple Music authentication errors stop the whole run.
        """
        playlists = self.spotify.playlists()
        if playlist_ids is not None:
            wanted = {parse_playlist_id(playlist_id) for playlist_id in playlist_ids}
            playlists = [playlist for playlist in playlists if playlist.id in wanted]

        results = []
        for playlist in playlists:
            try:
                results.append(self._transfer(playlist.id, playlist.name, dry_run))
            except (SpotifyAccessError, AppleMusicError) as exc:
                if isinstance(exc, AppleMusicError) and exc.is_auth_error:
                    raise
                self._echo(f"Could not transfer {playlist.name!r}: {exc}")
                results.append(TransferResult(playlist.id, playlist.name, error=str(exc)))

        if len(results) > 1:
            done = sum(1 for result in results if result.error is None)
            self._echo(f"\nTransferred {done} of {len(results)} playlists.")
        return results

    def _transfer(self, playlist_id: str, name: str, dry_run: bool) -> TransferResult:
        self._echo(f"\n{'Checking' if dry_run else 'Transferring'} {name!r}")
        tracks, skipped = self.spotify.tracks(playlist_id)
        result = TransferResult(playlist_id, name, skipped=skipped)

        catalog = self.apple.songs_by_isrc(track.isrc for track in tracks if track.isrc)
        song_ids = []
        for track in tracks:
            song_id = catalog.get(track.isrc.strip().upper()) if track.isrc else None
            if song_id:
                result.matched.append(track)
                song_ids.append(song_id)
            else:
                result.unmatched.append(track)

        if not dry_run:
            result.apple_playlist_id = self.apple.create_playlist(name)
            added = self.apple.add_tracks(result.apple_playlist_id, song_ids)
            for track, ok in zip(result.matched, added):
                (result.added if ok else result.failed).append(track)

        self._report(result, len(tracks), dry_run)
        return result

    def _report(self, result: TransferResult, total: int, dry_run: bool) -> None:
        if dry_run:
            self._echo(f"Found {len(result.matched)} of {total} songs on Apple Music")
        else:
            self._echo(f"Added {len(result.added)} of {total} songs")
        for track in result.unmatched:
            self._echo(f"  not on Apple Music: {track}")
        for track in result.failed:
            self._echo(f"  could not add: {track}")
        if result.skipped:
            self._echo(f"  skipped {result.skipped} local files, podcast episodes or unavailable tracks")
        if result.url:
            self._echo(f"Apple Music playlist: {result.url}")

    def _echo(self, message: Any) -> None:
        if self.verbose:
            print(message)
