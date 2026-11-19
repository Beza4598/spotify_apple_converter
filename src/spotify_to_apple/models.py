from dataclasses import dataclass, field
from typing import Optional

APPLE_PLAYLIST_URL = "https://music.apple.com/library/playlist/{}"


@dataclass(frozen=True)
class Track:
    name: str
    artist: str
    isrc: Optional[str] = None
    spotify_id: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.name} - {self.artist}" if self.artist else self.name


@dataclass(frozen=True)
class Playlist:
    id: str
    name: str
    owner: str = ""
    total_tracks: Optional[int] = None


@dataclass
class TransferResult:
    """What happened when one Spotify playlist was transferred.

    ``matched`` holds every track found on Apple Music. After a real transfer each
    matched track ends up in either ``added`` or ``failed``; a dry run leaves both empty.
    ``unmatched`` holds tracks with no ISRC or no Apple Music equivalent, and ``skipped``
    counts local files, podcast episodes and removed tracks.
    """

    spotify_playlist_id: str
    name: str
    apple_playlist_id: Optional[str] = None
    matched: list[Track] = field(default_factory=list)
    unmatched: list[Track] = field(default_factory=list)
    added: list[Track] = field(default_factory=list)
    failed: list[Track] = field(default_factory=list)
    skipped: int = 0
    error: Optional[str] = None

    @property
    def url(self) -> Optional[str]:
        return APPLE_PLAYLIST_URL.format(self.apple_playlist_id) if self.apple_playlist_id else None

    @property
    def ok(self) -> bool:
        return self.error is None and not self.failed
