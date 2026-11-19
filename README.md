# Spotify to Apple Music Converter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub issues](https://img.shields.io/github/issues-raw/Beza4598/spotify_apple_converter)](https://github.com/Beza4598/spotify_apple_converter/issues)
[![Codecov](https://img.shields.io/codecov/c/github/Beza4598/spotify_apple_converter)](https://codecov.io/gh/Beza4598/spotify_apple_converter)
[![Build Status](https://github.com/Beza4598/spotify_apple_converter/actions/workflows/workflow.yml/badge.svg?branch=main)](https://github.com/Beza4598/spotify_apple_converter/actions/workflows/workflow.yml)
[![PyPI](https://img.shields.io/pypi/v/spotify-to-apple-py)](https://pypi.org/project/spotify-to-apple-py/)
[![Docs](https://readthedocs.org/projects/spotify-apple-converter/badge/?version=latest)](https://spotify-apple-converter.readthedocs.io/en/latest/)

<!-- docs-start -->

A Python library and command-line tool that copies your Spotify playlists into your Apple Music library.

Each song is matched by its ISRC, the international code that identifies a specific recording, so the
Apple Music copy is the same recording rather than a lookalike from a search. Songs that can't be matched are
listed at the end of each transfer so you can add them by hand.

## Installation

```
pip install spotify-to-apple-py
```

Python 3.10 or newer is required.

## Setup

You need API credentials from both services. Put them in a `.env` file in the folder you run from, or export
them as environment variables.

```
# Spotify
SPOTIFY_CLIENT_ID=""
SPOTIFY_CLIENT_SECRET=""
SPOTIFY_REDIRECT_URI="http://127.0.0.1:8888/callback"

# Apple Music
APPLE_KEY_ID=""
APPLE_TEAM_ID=""
APPLE_USER_TOKEN=""
APPLE_PRIVATE_KEY_PATH="/path/to/AuthKey_XXXXXXXXXX.p8"
```

### Spotify

1. Create an app in the [Spotify developer dashboard](https://developer.spotify.com/dashboard) and copy its
   client ID and secret.
2. Add the redirect URI above to the app's settings. Spotify only accepts `http` redirects to a loopback
   address like `127.0.0.1`, not `localhost`.
3. While the app is in development mode, Spotify requires the app owner to have Premium and only lets the
   accounts listed under *User Management* sign in. It also only returns the songs in playlists you own or
   collaborate on, so playlists you merely follow are reported and skipped.

The first run opens a browser so you can sign in to Spotify. The token is cached in a `.cache` file
(`.cache-<user>` if you pass a user name), so later runs don't ask again.

### Apple Music

You need a membership in the [Apple Developer Program](https://developer.apple.com/programs/).

1. Create a MusicKit key under *Certificates, Identifiers & Profiles → Keys*. Download the `.p8` file and
   note the key ID and your team ID.
2. Generate a Music User Token for your Apple Music account. Apple doesn't provide a way to do this from
   Python, so follow the steps in [apple-musickit-example](https://github.com/KoleMyers/apple-musickit-example).

Instead of `APPLE_PRIVATE_KEY_PATH`, you can put the contents of the `.p8` file in `APPLE_PRIVATE_KEY`, which
is handy for CI secrets. The variable names used before 0.3 (`CLIENT_ID`, `CLIENT_SECRET`,
`CALLBACK_ADDRESS`) still work.

## Command line

```
spotify-to-apple list                                   # number your Spotify playlists
spotify-to-apple all                                    # transfer every playlist
spotify-to-apple all --select 1,3,5-7                   # transfer some of them
spotify-to-apple playlist https://open.spotify.com/playlist/5p1MWp58nGHAryTnJdmFCb?si=ed9f8a32d1534cb4
spotify-to-apple playlist <url> --name "African Soul"   # choose the Apple Music name
spotify-to-apple playlist <url> --dry-run               # see what would match, change nothing
```

Global options go before the command: `--key-file` points at the `.p8` key, `--storefront` sets the Apple
Music country (it's read from your account by default), and `--user` names the Spotify token cache.

```
$ spotify-to-apple playlist https://open.spotify.com/playlist/5p1MWp58nGHAryTnJdmFCb

Transferring 'Road Trip'
Added 41 of 43 songs
  not on Apple Music: Some Song - Some Artist
  not on Apple Music: Another Song - Another Artist
  skipped 1 local files, podcast episodes or unavailable tracks
Apple Music playlist: https://music.apple.com/library/playlist/p.XXXXXXXXXXXXXX
```

## Python

```python
from spotify_to_apple import SpotifyClient

client = SpotifyClient(path="AuthKey_XXXXXXXXXX.p8")

result = client.transfer_single_playlist("https://open.spotify.com/playlist/5p1MWp58nGHAryTnJdmFCb")
print(result.url)
for track in result.unmatched:
    print("Add by hand:", track)

results = client.transfer_all_playlists()
```

Both methods return `TransferResult` objects listing what was added, what couldn't be matched and what
failed. Pass `dry_run=True` to only match songs, or `verbose=False` to the constructor to turn off printing.
To pass credentials yourself instead of reading the environment, use `Credentials`:

```python
from spotify_to_apple import Credentials, SpotifyClient

credentials = Credentials(
    spotify_client_id="...",
    spotify_client_secret="...",
    apple_key_id="...",
    apple_team_id="...",
    apple_private_key=open("AuthKey_XXXXXXXXXX.p8").read(),
    apple_music_user_token="...",
)
client = SpotifyClient(credentials=credentials)
```

## How it works

1. Reads your playlists and their songs from Spotify, following every page of results. Local files, podcast
   episodes and songs that are no longer available are skipped.
2. Looks up the songs' ISRCs in the Apple Music catalog for your storefront, 25 at a time.
3. Creates a playlist in your Apple Music library and adds the matched songs in batches, in the original
   order. If Apple rejects a batch, its songs are retried one by one so a single bad song doesn't sink the rest.
4. When Apple rate-limits a request, waits as long as Apple asks and tries again.

## Upgrading from 0.2

- Import from `spotify_to_apple` instead of `spotify_client`.
- `transfer_single_playlist` names the Apple Music playlist after the Spotify playlist unless you pass a name.
- Both transfer methods return results instead of `None`, and print a summary instead of a line per song.
- The `transfer_all` constructor argument is gone. Pass playlist IDs to `transfer_all_playlists` to pick some.
- Python 3.7–3.9 and pandas are no longer needed or supported.

## Demo

These recordings are from version 0.2, which printed a line for each song instead of a summary.

![Transferring all playlists](https://raw.githubusercontent.com/Beza4598/spotify_apple_converter/main/docs/transfer-all.gif)

![Transferring a single playlist](https://raw.githubusercontent.com/Beza4598/spotify_apple_converter/main/docs/transfer-single.gif)

## Development

```
make develop    # install with development tools
make test       # run the tests (no API credentials needed)
make lint       # black and flake8
make annotate   # mypy
make coverage   # tests with coverage
make dist       # build and check the package
```

See [CONTRIBUTING.md](https://github.com/Beza4598/spotify_apple_converter/blob/main/CONTRIBUTING.md).
