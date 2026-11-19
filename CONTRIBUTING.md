# Contributing

Thanks for helping improve this project. Bug reports and pull requests are welcome.

## Getting set up

```
git clone https://github.com/Beza4598/spotify_apple_converter.git
cd spotify_apple_converter
python -m venv .venv && source .venv/bin/activate
make develop
```

The tests mock both APIs and generate a throwaway signing key, so `make test` works without any Spotify or
Apple Music credentials. To try a real transfer, set up credentials as described in the README.

## Before opening a pull request

- Run `make format`, `make lint`, `make annotate` and `make test`.
- Add tests for new behaviour and bug fixes.
- Update the README if you change how the library or command line is used, and add a line to `CHANGELOG.md`.

## Layout

- `src/spotify_to_apple/spotify.py` reads playlists from Spotify.
- `src/spotify_to_apple/apple.py` talks to the Apple Music API.
- `src/spotify_to_apple/converter.py` matches songs and runs transfers (`SpotifyClient`).
- `src/spotify_to_apple/cli.py` is the `spotify-to-apple` command.

## Releasing

1. Update the version in `pyproject.toml` and the changelog.
2. Run `make dist`, then `make publish`.
3. Tag the release, e.g. `git tag v0.3.0 && git push --tags`.
