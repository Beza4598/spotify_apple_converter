import argparse
import sys
from typing import Optional, Sequence

from .converter import SpotifyClient
from .errors import ConverterError


def parse_selection(text: str, count: int) -> list[int]:
    """Turn ``"1,3-5"`` into zero-based indexes, checking each is between 1 and ``count``."""
    indexes: list[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            if "-" in part:
                start, end = (int(bound) for bound in part.split("-", 1))
                numbers = list(range(start, end + 1))
            else:
                numbers = [int(part)]
        except ValueError:
            raise ValueError(f"Invalid selection {part!r}: use numbers like 1,3 or 2-5") from None
        for number in numbers:
            if not 1 <= number <= count:
                raise ValueError(f"Playlist number {number} is out of range (1-{count})")
            if number - 1 not in indexes:
                indexes.append(number - 1)
    if not indexes:
        raise ValueError("No playlists selected")
    return indexes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spotify-to-apple", description="Copy Spotify playlists into your Apple Music library."
    )
    parser.add_argument("--key-file", help="path to your Apple Music .p8 private key")
    parser.add_argument("--storefront", help="Apple Music storefront code such as us or gb (detected by default)")
    parser.add_argument("--user", help="name for the Spotify token cache file")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("list", help="list your Spotify playlists")

    all_parser = commands.add_parser("all", help="transfer all of your playlists")
    all_parser.add_argument("--select", help="only these playlists, by number from `list`, e.g. 1,3,5-7")
    all_parser.add_argument("--dry-run", action="store_true", help="match songs without creating anything")

    one_parser = commands.add_parser("playlist", help="transfer one playlist")
    one_parser.add_argument("url", help="Spotify playlist URL, URI or ID")
    one_parser.add_argument("--name", help="name for the Apple Music playlist (defaults to the Spotify name)")
    one_parser.add_argument("--dry-run", action="store_true", help="match songs without creating anything")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        client = SpotifyClient(args.user, args.key_file, storefront=args.storefront)
        if args.command == "list":
            for number, playlist in enumerate(client.list_playlists(), start=1):
                count = "" if playlist.total_tracks is None else f" ({playlist.total_tracks} tracks)"
                print(f"{number:>3}. {playlist.name}{count}")
            return 0
        if args.command == "all":
            playlist_ids = None
            if args.select:
                playlists = client.list_playlists()
                playlist_ids = [playlists[index].id for index in parse_selection(args.select, len(playlists))]
            results = client.transfer_all_playlists(playlist_ids, dry_run=args.dry_run)
            return 0 if all(result.ok for result in results) else 1
        result = client.transfer_single_playlist(args.url, args.name, dry_run=args.dry_run)
        return 0 if result.ok else 1
    except (ConverterError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
