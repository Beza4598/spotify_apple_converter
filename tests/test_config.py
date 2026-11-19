import pytest

from spotify_to_apple import ConfigurationError, Credentials
from spotify_to_apple.config import DEFAULT_REDIRECT_URI


def _set_apple(monkeypatch):
    monkeypatch.setenv("APPLE_KEY_ID", "KEY")
    monkeypatch.setenv("APPLE_TEAM_ID", "TEAM")
    monkeypatch.setenv("APPLE_USER_TOKEN", "user")


def test_reads_current_variable_names(monkeypatch, tmp_path):
    _set_apple(monkeypatch)
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "id")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "secret")
    monkeypatch.setenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:9000/cb")
    monkeypatch.setenv("APPLE_PRIVATE_KEY", "line1\\nline2")

    creds = Credentials.from_env(dotenv=False)

    assert creds.spotify_client_id == "id"
    assert creds.spotify_redirect_uri == "http://127.0.0.1:9000/cb"
    assert creds.apple_private_key == "line1\nline2"
    assert creds.apple_music_user_token == "user"


def test_falls_back_to_old_variable_names(monkeypatch):
    _set_apple(monkeypatch)
    monkeypatch.setenv("CLIENT_ID", "old-id")
    monkeypatch.setenv("CLIENT_SECRET", "old-secret")
    monkeypatch.setenv("CALLBACK_ADDRESS", "http://127.0.0.1:1234")
    monkeypatch.setenv("APPLE_PRIVATE_KEY", "key")

    creds = Credentials.from_env(dotenv=False)

    assert (creds.spotify_client_id, creds.spotify_client_secret) == ("old-id", "old-secret")
    assert creds.spotify_redirect_uri == "http://127.0.0.1:1234"


def test_reads_private_key_from_a_file(monkeypatch, tmp_path):
    key_file = tmp_path / "key.p8"
    key_file.write_text("from file")
    monkeypatch.setenv("APPLE_PRIVATE_KEY", "from env")

    assert Credentials.from_env(key_file, spotify=False, apple=False, dotenv=False).apple_private_key == "from file"

    monkeypatch.setenv("APPLE_PRIVATE_KEY_PATH", str(key_file))
    assert Credentials.from_env(spotify=False, apple=False, dotenv=False).apple_private_key == "from file"


def test_missing_key_file_is_a_configuration_error(tmp_path):
    with pytest.raises(ConfigurationError, match="Could not read"):
        Credentials.from_env(tmp_path / "missing.p8", dotenv=False)


def test_lists_every_missing_value(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "id")

    with pytest.raises(ConfigurationError) as info:
        Credentials.from_env(dotenv=False)

    message = str(info.value)
    for name in ("SPOTIFY_CLIENT_SECRET", "APPLE_KEY_ID", "APPLE_TEAM_ID", "APPLE_USER_TOKEN", "APPLE_PRIVATE_KEY"):
        assert name in message
    assert "SPOTIFY_CLIENT_ID," not in message


def test_only_checks_the_requested_services(monkeypatch):
    _set_apple(monkeypatch)
    monkeypatch.setenv("APPLE_PRIVATE_KEY", "key")

    creds = Credentials.from_env(spotify=False, dotenv=False)

    assert creds.spotify_client_id is None
    assert creds.spotify_redirect_uri == DEFAULT_REDIRECT_URI


def test_loads_a_dotenv_file(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("SPOTIFY_CLIENT_ID=from-dotenv\nSPOTIFY_CLIENT_SECRET=s\n")
    monkeypatch.chdir(tmp_path)

    creds = Credentials.from_env(apple=False)

    assert creds.spotify_client_id == "from-dotenv"
