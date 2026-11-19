import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from .errors import ConfigurationError

DEFAULT_REDIRECT_URI = "http://127.0.0.1:8888/callback"

_ENV_NAMES = {
    "spotify_client_id": ("SPOTIFY_CLIENT_ID", "CLIENT_ID"),
    "spotify_client_secret": ("SPOTIFY_CLIENT_SECRET", "CLIENT_SECRET"),
    "spotify_redirect_uri": ("SPOTIFY_REDIRECT_URI", "CALLBACK_ADDRESS"),
    "apple_key_id": ("APPLE_KEY_ID",),
    "apple_team_id": ("APPLE_TEAM_ID",),
    "apple_music_user_token": ("APPLE_USER_TOKEN",),
}
_SPOTIFY_FIELDS = ("spotify_client_id", "spotify_client_secret")
_APPLE_FIELDS = ("apple_key_id", "apple_team_id", "apple_private_key", "apple_music_user_token")


def _env(names: tuple[str, ...]) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


@dataclass
class Credentials:
    """Spotify and Apple Music credentials.

    Create one directly, or use :meth:`from_env` to read them from environment
    variables and an optional ``.env`` file.
    """

    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    apple_key_id: Optional[str] = None
    apple_team_id: Optional[str] = None
    apple_private_key: Optional[str] = None
    apple_music_user_token: Optional[str] = None
    spotify_redirect_uri: str = DEFAULT_REDIRECT_URI

    @classmethod
    def from_env(
        cls,
        private_key_path: Optional[Union[str, Path]] = None,
        *,
        spotify: bool = True,
        apple: bool = True,
        dotenv: bool = True,
    ) -> "Credentials":
        """Read credentials from the environment.

        Args:
            private_key_path: Path to the Apple Music ``.p8`` key. Falls back to
                ``APPLE_PRIVATE_KEY_PATH``, then to the key itself in ``APPLE_PRIVATE_KEY``.
            spotify: Require the Spotify credentials.
            apple: Require the Apple Music credentials.
            dotenv: Load a ``.env`` file from the current directory first.

        Raises:
            ConfigurationError: A required value is missing.
        """
        if dotenv:
            from dotenv import find_dotenv, load_dotenv

            load_dotenv(find_dotenv(usecwd=True))

        values = {name: _env(env_names) for name, env_names in _ENV_NAMES.items()}
        key_path = private_key_path or os.environ.get("APPLE_PRIVATE_KEY_PATH")
        if key_path:
            try:
                values["apple_private_key"] = Path(key_path).expanduser().read_text()
            except OSError as exc:
                raise ConfigurationError(f"Could not read Apple private key file {key_path}: {exc}") from exc
        else:
            raw_key = os.environ.get("APPLE_PRIVATE_KEY")
            values["apple_private_key"] = raw_key.replace("\\n", "\n") if raw_key else None

        required = (_SPOTIFY_FIELDS if spotify else ()) + (_APPLE_FIELDS if apple else ())
        missing = [_describe(name) for name in required if not values[name]]
        if missing:
            raise ConfigurationError("Missing configuration: " + ", ".join(missing))

        return cls(
            spotify_client_id=values["spotify_client_id"],
            spotify_client_secret=values["spotify_client_secret"],
            apple_key_id=values["apple_key_id"],
            apple_team_id=values["apple_team_id"],
            apple_private_key=values["apple_private_key"],
            apple_music_user_token=values["apple_music_user_token"],
            spotify_redirect_uri=values["spotify_redirect_uri"] or DEFAULT_REDIRECT_URI,
        )


def _describe(field_name: str) -> str:
    if field_name == "apple_private_key":
        return "APPLE_PRIVATE_KEY_PATH (or APPLE_PRIVATE_KEY)"
    return _ENV_NAMES[field_name][0]
