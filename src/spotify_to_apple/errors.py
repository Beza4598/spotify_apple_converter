class ConverterError(Exception):
    """Base class for every error raised by this library."""


class ConfigurationError(ConverterError):
    """Required credentials or settings are missing."""


class SpotifyAccessError(ConverterError):
    """Spotify refused to return a playlist or its contents."""


class AppleMusicError(ConverterError):
    """The Apple Music API returned an error response."""

    def __init__(self, status: int, message: str):
        super().__init__(f"Apple Music API returned {status}: {message}")
        self.status = status

    @property
    def is_auth_error(self) -> bool:
        return self.status in (401, 403)
