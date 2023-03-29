import unittest
import pandas as pd
from unittest.mock import patch
from src.spotify_client import SpotifyClient
from unittest.mock import MagicMock
from io import StringIO
from spotipy.oauth2 import SpotifyOAuth, CacheFileHandler

class TestSpotifyClient(unittest.TestCase):
    def test_get_user_info(self):
        auth_manager_mock = MagicMock(spec=SpotifyOAuth)
        cache_handler_mock = MagicMock(spec=CacheFileHandler)
        auth_manager_mock.cache_handler = cache_handler_mock
        auth_manager_mock.get_cached_token.return_value = {"access_token": "fake_access_token"}
        
        mock_user = "bezamufc"
        sp = SpotifyClient("bezamufc", auth_manager=auth_manager_mock)

        with patch("sys.stdin", StringIO(mock_user)):
            self.assertEqual(sp.get_user_info(), mock_user)

    def test_generate_token(self):
        auth_manager_mock = MagicMock(spec=SpotifyOAuth)
        cache_handler_mock = MagicMock(spec=CacheFileHandler)
        auth_manager_mock.cache_handler = cache_handler_mock
        auth_manager_mock.get_cached_token.return_value = {"access_token": "fake_access_token"}
        client = SpotifyClient("testuser", auth_manager=auth_manager_mock)
        token = client._generate_token("user-library-read")
        self.assertIsNotNone(token)

    @patch("spotipy.Spotify", autospec=True)
    def test_get_user_playlists_sp(self, mock_spotify):
        auth_manager_mock = MagicMock(spec=SpotifyOAuth)
        cache_handler_mock = MagicMock(spec=CacheFileHandler)
        auth_manager_mock.cache_handler = cache_handler_mock
        auth_manager_mock.get_cached_token.return_value = {"access_token": "fake_access_token"}

        client = SpotifyClient("testuser", auth_manager=auth_manager_mock)
        mock_sp = MagicMock()
        mock_sp.current_user_playlists.return_value = {
            "items": [
                {"name": "Playlist 1", "id": "123"},
                {"name": "Playlist 2", "id": "456"},
            ]
        }
        mock_spotify.return_value = mock_sp
        expected_df = pd.DataFrame(
            {
                "playlist_id": ["123", "456"],
                "playlist_name": ["Playlist 1", "Playlist 2"],
            }
        )

        result_df = client.get_user_playlists_sp()
        pd.testing.assert_frame_equal(result_df, expected_df)

    def test_select_all_playlists(self):
        auth_manager_mock = MagicMock(spec=SpotifyOAuth)
        cache_handler_mock = MagicMock(spec=CacheFileHandler)
        auth_manager_mock.cache_handler = cache_handler_mock
        auth_manager_mock.get_cached_token.return_value = {"access_token": "fake_access_token"}

        sp = SpotifyClient("testuser", auth_manager=auth_manager_mock)
        playlists = ["Playlist 1", "Playlist 2", "Playlist 3"]
        expected_result = [0, 1, 2]
        result = sp.get_user_choices(playlists)
        self.assertEqual(expected_result, result)

    @patch('builtins.input', return_value='1,3')
    def test_get_user_choices(self, mock_input):
        auth_manager_mock = MagicMock(spec=SpotifyOAuth)
        cache_handler_mock = MagicMock(spec=CacheFileHandler)
        auth_manager_mock.cache_handler = cache_handler_mock
        auth_manager_mock.get_cached_token.return_value = {"access_token": "fake_access_token"}

        sp = SpotifyClient("testuser", transfer_all=False, auth_manager=auth_manager_mock)
        playlists = ['Playlist 1', 'Playlist 2', 'Playlist 3', 'Playlist 4']
        expected_result = ['1', '3']
        result = sp.get_user_choices(playlists)
        self.assertEqual(result, expected_result)

    @patch('builtins.input', return_value='1, 4, 2')
    def test_get_user_choices_multiple(self, mock_input):
        auth_manager_mock = MagicMock(spec=SpotifyOAuth)
        cache_handler_mock = MagicMock(spec=CacheFileHandler)
        auth_manager_mock.cache_handler = cache_handler_mock
        auth_manager_mock.get_cached_token.return_value = {"access_token": "fake_access_token"}

        sp = SpotifyClient("testuser", transfer_all=False, auth_manager=auth_manager_mock)
        playlists = ['Playlist 1', 'Playlist 2', 'Playlist 3', 'Playlist 4', 'Playlist 5']
        expected_result = list(map(int, ['1', '4', '2']))
        result = list(map(int, sp.get_user_choices(playlists)))
        self.assertEqual(result, expected_result)

    def test_spotifyToAppleMusicUsingISRC(self):
        auth_manager_mock = MagicMock(spec=SpotifyOAuth)
        cache_handler_mock = MagicMock(spec=CacheFileHandler)
        auth_manager_mock.cache_handler = cache_handler_mock
        auth_manager_mock.get_cached_token.return_value = {"access_token": "fake_access_token"}

        client = SpotifyClient("testuser", transfer_all=False, auth_manager=auth_manager_mock)
        tracks = pd.DataFrame(
            {
                "track_ids": ["1", "2"],
                "track_titles": ["Track 1", "Track 2"],
                "track_first_artists": ["Artist 1", "Artist 2"],
                "track_popularity": [80, 90],
                "track_isrc": ["ISRC1", "ISRC2"],
            }
        )
        with patch('applemusicpy.AppleMusic.songs_by_isrc', return_value={"data": []}):
            track_dataframe = client.spotifyToAppleMusicUsingISRC(tracks)

        self.assertEqual(len(track_dataframe), 0)

    def test_create_new_playlist(self):
        auth_manager_mock = MagicMock(spec=SpotifyOAuth)
        cache_handler_mock = MagicMock(spec=CacheFileHandler)
        auth_manager_mock.cache_handler = cache_handler_mock
        auth_manager_mock.get_cached_token.return_value = {"access_token": "fake_access_token"}

        client = SpotifyClient("testuser", transfer_all=False, auth_manager=auth_manager_mock)

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {"data": [{"id": "new_playlist_id"}]}
            result = client.create_new_playlist("Test Playlist")

        self.assertEqual(result, "new_playlist_id")

    def test_insert_track_to_playlist(self):
        auth_manager_mock = MagicMock(spec=SpotifyOAuth)
        cache_handler_mock = MagicMock(spec=CacheFileHandler)
        auth_manager_mock.cache_handler = cache_handler_mock
        auth_manager_mock.get_cached_token.return_value = {"access_token": "fake_access_token"}

        client = SpotifyClient("testuser", transfer_all=False, auth_manager=auth_manager_mock)

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 204
            result = client.insert_track_to_playlist("test_playlist_id", "test_track_id")

        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
