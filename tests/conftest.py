import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from spotify_to_apple import AppleMusicClient, Credentials


@pytest.fixture(scope="session")
def ec_key():
    key = ec.generate_private_key(ec.SECP256R1())
    private_pem = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()
    public_pem = (
        key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    return private_pem, public_pem


@pytest.fixture
def credentials(ec_key):
    return Credentials(
        spotify_client_id="spotify-id",
        spotify_client_secret="spotify-secret",
        apple_key_id="KEY123",
        apple_team_id="TEAM123",
        apple_private_key=ec_key[0],
        apple_music_user_token="user-token",
    )


@pytest.fixture
def sleeps():
    return []


@pytest.fixture
def apple(credentials, sleeps):
    return AppleMusicClient.from_credentials(credentials, storefront="us", sleep=sleeps.append)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in (
        "SPOTIFY_CLIENT_ID",
        "SPOTIFY_CLIENT_SECRET",
        "SPOTIFY_REDIRECT_URI",
        "CLIENT_ID",
        "CLIENT_SECRET",
        "CALLBACK_ADDRESS",
        "APPLE_KEY_ID",
        "APPLE_TEAM_ID",
        "APPLE_USER_TOKEN",
        "APPLE_PRIVATE_KEY",
        "APPLE_PRIVATE_KEY_PATH",
    ):
        monkeypatch.delenv(name, raising=False)
