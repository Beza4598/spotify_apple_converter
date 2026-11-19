# Changelog

## 0.3.0

### Fixed
- Playlist URLs with a `?si=` share code or a trailing slash, including the README example, now work.
- All of a user's playlists are transferred, not just the first 50.
- Private and collaborative playlists can be read (adds the `playlist-read-private` and
  `playlist-read-collaborative` scopes).
- Local files, podcast episodes, removed tracks and tracks without an ISRC no longer crash a transfer.
- Uses Spotify's `/playlists/{id}/items` endpoint and `item` field, which replaced `/tracks` and `track` for
  development mode apps in February 2026.
- Apple Music errors are raised with a useful message instead of creating a playlist called "Unauthorized".
- Rate-limited Apple Music requests (HTTP 429) are retried after the requested delay.
- A `.env` file is read from the current folder rather than from the installed package's folder.
- The Apple developer token is refreshed before it expires.
- The package installs on current Python versions: dependencies are no longer pinned to 2023 releases.
- The package no longer installs a bare `spotify_client.py` and `__init__.py` into site-packages.

### Added
- `spotify-to-apple` command with `list`, `all` (with `--select`) and `playlist` subcommands.
- `TransferResult` return values listing added, unmatched, failed and skipped songs, plus a printed summary.
- `dry_run` option to match songs without changing anything.
- `Credentials` for passing credentials directly, and `APPLE_PRIVATE_KEY_PATH`.
- The Apple Music storefront is read from the user's account, or set with `storefront=`.
- Songs are matched 25 ISRCs per request and added to playlists in batches.
- The Spotify playlist name is used for the Apple Music playlist by default.
- Type hints and a `py.typed` marker.

### Changed
- The import is now `from spotify_to_apple import SpotifyClient`.
- Spotify environment variables are now `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` and
  `SPOTIFY_REDIRECT_URI`. The old names still work.
- Removed the unused `transfer_all` constructor argument and the pandas and apple-music-python dependencies.
- Requires Python 3.10 or newer.
- The tests run without real credentials, and CI tests Python 3.10 to 3.14.
