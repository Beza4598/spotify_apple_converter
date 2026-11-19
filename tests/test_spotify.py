from unittest.mock import MagicMock

import pytest
from spotipy.exceptions import SpotifyException

from spotify_to_apple import SpotifyAccessError, Track, parse_playlist_id
from spotify_to_apple.spotify import SCOPES, SpotifyLibrary, create_spotify

PLAYLIST_ID = "5p1MWp58nGHAryTnJdmFCb"


@pytest.mark.parametrize(
    "value",
    [
        f"https://open.spotify.com/playlist/{PLAYLIST_ID}?si=ed9f8a32d1534cb4",
        f"https://open.spotify.com/playlist/{PLAYLIST_ID}/",
        f"https://open.spotify.com/intl-de/playlist/{PLAYLIST_ID}",
        f"https://open.spotify.com/user/someone/playlist/{PLAYLIST_ID}",
        f"open.spotify.com/playlist/{PLAYLIST_ID}",
        f"spotify:playlist:{PLAYLIST_ID}",
        f"spotify:user:someone:playlist:{PLAYLIST_ID}",
        f"  {PLAYLIST_ID}  ",
    ],
)
def test_parse_playlist_id(value):
    assert parse_playlist_id(value) == PLAYLIST_ID


@pytest.mark.parametrize(
    "value",
    [
        "",
        "https://open.spotify.com/album/4aawyAB9vmqN3uQ7FjRGTy",
        "https://open.spotify.com/playlist/",
        "spotify:track:4uLU6hMCjMI75M1A2tKUQC",
        "not a playlist",
    ],
)
def test_parse_playlist_id_rejects_other_input(value):
    with pytest.raises(ValueError):
        parse_playlist_id(value)


def _page(items, next_url=None):
    return {"items": items, "next": next_url}


def test_playlists_follows_every_page():
    sp = MagicMock()
    sp.current_user_playlists.return_value = _page(
        [{"id": "a", "name": "One", "owner": {"display_name": "me"}, "items": {"total": 3}}], "page-2"
    )
    sp.next.return_value = _page([{"id": "b", "name": "Two", "tracks": {"total": 7}}, None])

    playlists = SpotifyLibrary(sp).playlists()

    assert [(p.id, p.name, p.total_tracks) for p in playlists] == [("a", "One", 3), ("b", "Two", 7)]
    assert playlists[0].owner == "me"
    sp.current_user_playlists.assert_called_once_with(limit=50)


def test_tracks_handles_new_and_old_item_keys_and_skips_non_songs():
    sp = MagicMock()
    song = {"type": "track", "name": "Mali Men", "artists": [{"name": "Artist"}], "external_ids": {"isrc": "AB1"}}
    sp.playlist_items.return_value = _page(
        [
            {"item": {**song, "id": "1"}},
            {"track": {**song, "id": "2", "name": "Old Key"}},
            {"item": None},
            {"is_local": True, "item": {**song, "id": None, "is_local": True}},
            {"item": {"type": "episode", "name": "Podcast"}},
        ],
        "page-2",
    )
    sp.next.return_value = _page([{"item": {"type": "track", "id": "3", "name": "No ISRC", "artists": []}}])

    tracks, skipped = SpotifyLibrary(sp).tracks(PLAYLIST_ID)

    assert tracks == [
        Track("Mali Men", "Artist", "AB1", "1"),
        Track("Old Key", "Artist", "AB1", "2"),
        Track("No ISRC", "", None, "3"),
    ]
    assert skipped == 3
    sp.playlist_items.assert_called_once_with(PLAYLIST_ID, limit=100, additional_types=("track",))


@pytest.mark.parametrize("status, text", [(403, "development mode"), (404, "not found")])
def test_tracks_turns_access_errors_into_spotify_access_error(status, text):
    sp = MagicMock()
    sp.playlist_items.side_effect = SpotifyException(status, -1, "nope")

    with pytest.raises(SpotifyAccessError, match=text):
        SpotifyLibrary(sp).tracks(PLAYLIST_ID)


def test_other_spotify_errors_propagate():
    sp = MagicMock()
    sp.playlist_items.side_effect = SpotifyException(500, -1, "boom")

    with pytest.raises(SpotifyException):
        SpotifyLibrary(sp).tracks(PLAYLIST_ID)


def test_playlist_name():
    sp = MagicMock()
    sp.playlist.return_value = {"name": "African Soul"}

    assert SpotifyLibrary(sp).playlist_name(PLAYLIST_ID) == "African Soul"
    sp.playlist.assert_called_once_with(PLAYLIST_ID, fields="name")


def test_create_spotify_requests_playlist_scopes(credentials, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sp = create_spotify(credentials, user="beza")

    auth = sp.auth_manager
    assert set(auth.scope.split()) == set(SCOPES.split())
    assert auth.redirect_uri == "http://127.0.0.1:8888/callback"
    assert auth.cache_handler.cache_path == ".cache-beza"


def test_create_spotify_needs_credentials_or_auth_manager():
    with pytest.raises(ValueError):
        create_spotify()
