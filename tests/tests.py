import unittest
import pandas as pd
from unittest.mock import patch
from src.spotify_client import SpotifyClient
from unittest.mock import MagicMock
from io import StringIO


class TestSpotifyClient(unittest.TestCase):

    def test_get_user_info(self):

        mock_user = "bezamufc"
        sp = SpotifyClient("bezamufc")

        with patch("sys.stdin", StringIO(mock_user)):
            self.assertEqual(sp.get_user_info(), mock_user)
    
    def test_generate_token(self):
        client = SpotifyClient('testuser')
        token = client._generate_token('user-library-read')
        self.assertIsNotNone(token)

    @patch('spotipy.Spotify', autospec=True)
    def test_get_user_playlists_sp(self, mock_spotify):
        client = SpotifyClient('testuser')
        mock_sp = MagicMock()
        mock_sp.current_user_playlists.return_value = {
            'items': [
                {'name': 'Playlist 1', 'id': '123'},
                {'name': 'Playlist 2', 'id': '456'}
            ]
        }
        mock_spotify.return_value = mock_sp
        expected_df = pd.DataFrame({
            'playlist_id': ['123', '456'],
            'playlist_name': ['Playlist 1', 'Playlist 2']
        })

        result_df = client.get_user_playlists_sp()
        pd.testing.assert_frame_equal(result_df, expected_df)
        
    def test_select_all_playlists(self):
        sp = SpotifyClient('testuser')
        playlists = ["Playlist 1", "Playlist 2", "Playlist 3"]
        with patch('builtins.input', side_effect=["A"]):
            u_choice = sp.get_user_choices(playlists)
        self.assertEqual(u_choice, [0, 1, 2])

    def test_select_specific_playlists(self):
        sp = SpotifyClient('testuser')
        playlists = ["Playlist 1", "Playlist 2", "Playlist 3"]
        with patch('builtins.input', side_effect=["S", "1,2"]):
            u_choice = sp.get_user_choices(playlists)
        self.assertEqual(u_choice, ["1", "2"])

    def test_invalid_input(self):
        sp = SpotifyClient('testuser')
        playlists = ["Playlist 1", "Playlist 2", "Playlist 3"]
        with patch('builtins.input', side_effect=["invalid"]):
            with self.assertRaises(SystemExit):
                sp.get_user_choices(playlists)


if __name__ == '__main__':
    unittest.main()