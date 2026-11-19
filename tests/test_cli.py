from unittest.mock import MagicMock

import pytest

from spotify_to_apple import ConfigurationError, Playlist, TransferResult, cli


@pytest.mark.parametrize(
    "text, expected",
    [("1", [0]), ("1,3", [0, 2]), (" 3, 1 ,", [2, 0]), ("2-4", [1, 2, 3]), ("1,1-2", [0, 1])],
)
def test_parse_selection(text, expected):
    assert cli.parse_selection(text, 5) == expected


@pytest.mark.parametrize("text", ["0", "6", "a", "1-x", ",", ""])
def test_parse_selection_rejects_bad_input(text):
    with pytest.raises(ValueError):
        cli.parse_selection(text, 5)


@pytest.fixture
def client(monkeypatch):
    instance = MagicMock()
    instance.list_playlists.return_value = [Playlist("a" * 22, "One", total_tracks=3), Playlist("b" * 22, "Two")]
    factory = MagicMock(return_value=instance)
    monkeypatch.setattr(cli, "SpotifyClient", factory)
    instance.factory = factory
    return instance


def test_list(client, capsys):
    assert cli.main(["--key-file", "k.p8", "--storefront", "gb", "list"]) == 0

    client.factory.assert_called_once_with(None, "k.p8", storefront="gb")
    assert capsys.readouterr().out.splitlines() == ["  1. One (3 tracks)", "  2. Two"]


def test_all_with_selection(client):
    client.transfer_all_playlists.return_value = [TransferResult("b" * 22, "Two")]

    assert cli.main(["all", "--select", "2", "--dry-run"]) == 0

    client.transfer_all_playlists.assert_called_once_with(["b" * 22], dry_run=True)


def test_all_exits_non_zero_when_a_playlist_fails(client):
    client.transfer_all_playlists.return_value = [TransferResult("a" * 22, "One", error="nope")]

    assert cli.main(["all"]) == 1


def test_playlist(client):
    client.transfer_single_playlist.return_value = TransferResult("a" * 22, "One")

    assert cli.main(["playlist", "https://open.spotify.com/playlist/x", "--name", "Mix"]) == 0

    client.transfer_single_playlist.assert_called_once_with("https://open.spotify.com/playlist/x", "Mix", dry_run=False)


def test_errors_are_printed_without_a_traceback(client, capsys):
    client.factory.side_effect = ConfigurationError("Missing configuration: APPLE_KEY_ID")

    assert cli.main(["list"]) == 1
    assert capsys.readouterr().err == "error: Missing configuration: APPLE_KEY_ID\n"
