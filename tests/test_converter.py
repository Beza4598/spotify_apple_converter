from unittest.mock import MagicMock

import pytest
from spotipy.exceptions import SpotifyException

from spotify_to_apple import AppleMusicError, ConfigurationError, SpotifyClient, Track

PLAYLIST_ID = "5p1MWp58nGHAryTnJdmFCb"
OTHER_ID = "37i9dQZF1DXcBWIGoYBM5M"


def _item(name, isrc, track_id):
    return {"item": {"type": "track", "id": track_id, "name": name, "artists": [{"name": "A"}], "external_ids": isrc}}


class FakeApple:
    def __init__(self, catalog=None, fail=()):
        self.catalog = catalog or {}
        self.fail = set(fail)
        self.created = []
        self.added = []

    def songs_by_isrc(self, isrcs):
        return {isrc.upper(): self.catalog[isrc.upper()] for isrc in isrcs if isrc.upper() in self.catalog}

    def create_playlist(self, name):
        self.created.append(name)
        return f"p.{len(self.created)}"

    def add_tracks(self, playlist_id, song_ids):
        self.added.append((playlist_id, list(song_ids)))
        return [song_id not in self.fail for song_id in song_ids]


@pytest.fixture
def sp():
    sp = MagicMock()
    sp.playlist.return_value = {"name": "African Soul"}
    sp.playlist_items.return_value = {
        "items": [
            _item("Fala", {"isrc": "ab1"}, "1"),
            _item("Mali Men", {"isrc": "AB2"}, "2"),
            _item("Unknown", {"isrc": "ZZ9"}, "3"),
            _item("No ISRC", {}, "4"),
            {"item": None},
        ],
        "next": None,
    }
    sp.current_user_playlists.return_value = {
        "items": [{"id": PLAYLIST_ID, "name": "Mine"}, {"id": OTHER_ID, "name": "Not Mine"}],
        "next": None,
    }
    return sp


def test_transfer_single_playlist(sp, capsys):
    apple = FakeApple({"AB1": "100", "AB2": "200"})
    client = SpotifyClient(spotify=sp, apple=apple)

    result = client.transfer_single_playlist(f"https://open.spotify.com/playlist/{PLAYLIST_ID}?si=x")

    assert apple.created == ["African Soul"]
    assert apple.added == [("p.1", ["100", "200"])]
    assert [t.name for t in result.added] == ["Fala", "Mali Men"]
    assert [t.name for t in result.unmatched] == ["Unknown", "No ISRC"]
    assert result.skipped == 1
    assert result.url == "https://music.apple.com/library/playlist/p.1"
    assert result.ok
    out = capsys.readouterr().out
    assert "Added 2 of 4 songs" in out
    assert "not on Apple Music: Unknown - A" in out
    assert result.url in out


def test_transfer_single_playlist_uses_given_name_and_reports_failures(sp):
    apple = FakeApple({"AB1": "100", "AB2": "200"}, fail={"200"})
    client = SpotifyClient(spotify=sp, apple=apple, verbose=False)

    result = client.transfer_single_playlist(PLAYLIST_ID, "Renamed")

    assert apple.created == ["Renamed"]
    sp.playlist.assert_not_called()
    assert result.failed == [Track("Mali Men", "A", "AB2", "2")]
    assert not result.ok


def test_dry_run_creates_nothing(sp, capsys):
    apple = FakeApple({"AB1": "100"})
    client = SpotifyClient(spotify=sp, apple=apple)

    result = client.transfer_single_playlist(PLAYLIST_ID, dry_run=True)

    assert apple.created == [] and apple.added == []
    assert [t.name for t in result.matched] == ["Fala"]
    assert result.added == [] and result.url is None
    assert "Found 1 of 4 songs" in capsys.readouterr().out


def test_transfer_single_playlist_rejects_bad_urls(sp):
    client = SpotifyClient(spotify=sp, apple=FakeApple(), verbose=False)

    with pytest.raises(ValueError):
        client.transfer_single_playlist("https://open.spotify.com/album/4aawyAB9vmqN3uQ7FjRGTy")


def test_transfer_all_continues_past_playlists_spotify_refuses(sp):
    def items(playlist_id, **kwargs):
        if playlist_id == OTHER_ID:
            raise SpotifyException(403, -1, "forbidden")
        return {"items": [_item("Fala", {"isrc": "AB1"}, "1")], "next": None}

    sp.playlist_items.side_effect = items
    apple = FakeApple({"AB1": "100"})
    client = SpotifyClient(spotify=sp, apple=apple, verbose=False)

    results = client.transfer_all_playlists()

    assert [r.name for r in results] == ["Mine", "Not Mine"]
    assert results[0].ok and len(results[0].added) == 1
    assert "development mode" in results[1].error
    assert apple.created == ["Mine"]


def test_transfer_all_stops_on_apple_auth_errors(sp):
    apple = FakeApple()
    apple.create_playlist = MagicMock(side_effect=AppleMusicError(401, "bad token"))
    client = SpotifyClient(spotify=sp, apple=apple, verbose=False)

    with pytest.raises(AppleMusicError):
        client.transfer_all_playlists()
    assert apple.create_playlist.call_count == 1


def test_transfer_all_records_other_apple_errors(sp):
    apple = FakeApple()
    apple.create_playlist = MagicMock(side_effect=AppleMusicError(500, "down"))
    client = SpotifyClient(spotify=sp, apple=apple, verbose=False)

    results = client.transfer_all_playlists()

    assert all("500" in r.error for r in results)


def test_transfer_all_can_be_limited_to_some_playlists(sp):
    apple = FakeApple()
    client = SpotifyClient(spotify=sp, apple=apple, verbose=False)

    results = client.transfer_all_playlists([f"spotify:playlist:{OTHER_ID}"])

    assert [r.name for r in results] == ["Not Mine"]
    assert apple.created == ["Not Mine"]


def test_list_playlists(sp):
    client = SpotifyClient(spotify=sp, apple=FakeApple())

    assert [p.name for p in client.list_playlists()] == ["Mine", "Not Mine"]


def test_reads_credentials_from_the_environment(monkeypatch, ec_key, tmp_path):
    key_file = tmp_path / "AuthKey.p8"
    key_file.write_text(ec_key[0])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "id")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "secret")
    monkeypatch.setenv("APPLE_KEY_ID", "KEY")
    monkeypatch.setenv("APPLE_TEAM_ID", "TEAM")
    monkeypatch.setenv("APPLE_USER_TOKEN", "user")

    client = SpotifyClient("beza", key_file, storefront="gb")

    assert client.apple.team_id == "TEAM"
    assert client.apple.storefront == "gb"
    assert client.spotify.sp.auth_manager.client_id == "id"


def test_missing_credentials_are_reported(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ConfigurationError, match="SPOTIFY_CLIENT_ID.*APPLE_TEAM_ID"):
        SpotifyClient()


def test_spotify_credentials_are_optional_with_an_auth_manager(tmp_path, monkeypatch, ec_key):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APPLE_KEY_ID", "KEY")
    monkeypatch.setenv("APPLE_TEAM_ID", "TEAM")
    monkeypatch.setenv("APPLE_USER_TOKEN", "user")
    monkeypatch.setenv("APPLE_PRIVATE_KEY", ec_key[0])
    auth_manager = MagicMock()

    client = SpotifyClient(auth_manager=auth_manager)

    assert client.spotify.sp.auth_manager is auth_manager
