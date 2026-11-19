"""Transfer Spotify playlists to Apple Music."""

from importlib.metadata import PackageNotFoundError, version

from .apple import AppleMusicClient
from .config import Credentials
from .converter import SpotifyClient
from .errors import AppleMusicError, ConfigurationError, ConverterError, SpotifyAccessError
from .models import Playlist, Track, TransferResult
from .spotify import parse_playlist_id

try:
    __version__ = version("spotify-to-apple-py")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "AppleMusicClient",
    "AppleMusicError",
    "ConfigurationError",
    "ConverterError",
    "Credentials",
    "Playlist",
    "SpotifyAccessError",
    "SpotifyClient",
    "Track",
    "TransferResult",
    "parse_playlist_id",
    "__version__",
]
