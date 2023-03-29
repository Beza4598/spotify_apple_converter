import unittest
import pandas as pd
from unittest.mock import patch
from src.spotify_client import SpotifyClient
from unittest.mock import MagicMock
from io import StringIO
from contextlib import redirect_stdout


class TestSpotifyClient(unittest.TestCase):
    def test_get_user_info(self):
        mock_user = "bezamufc"
        sp = SpotifyClient("bezamufc")

        with patch("sys.stdin", StringIO(mock_user)):
            self.assertEqual(sp.get_user_info(), mock_user)

    def test_generate_token(self):
        client = SpotifyClient("testuser")
        token = client._generate_token("user-library-read")
        self.assertIsNotNone(token)

    @patch("spotipy.Spotify", autospec=True)
    def test_get_user_playlists_sp(self, mock_spotify):
        client = SpotifyClient("testuser")
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
        sp = SpotifyClient("testuser")
        playlists = ["Playlist 1", "Playlist 2", "Playlist 3"]
        expected_result = [0, 1, 2]
        result = sp.get_user_choices(playlists)
        self.assertEqual(expected_result, result)

    @patch('builtins.input', return_value='1,3')
    def test_get_user_choices(self, mock_input):
        sp = SpotifyClient("testuser", transfer_all=False)
        playlists = ['Playlist 1', 'Playlist 2', 'Playlist 3', 'Playlist 4']
        expected_result = ['1', '3']
        result = sp.get_user_choices(playlists)
        self.assertEqual(result, expected_result)

    @patch('builtins.input', return_value='1, 4, 2')
    def test_get_user_choices_multiple(self, mock_input):
        sp = SpotifyClient("testuser", transfer_all=False)
        playlists = ['Playlist 1', 'Playlist 2', 'Playlist 3', 'Playlist 4', 'Playlist 5']
        expected_result = list(map(int, ['1', '4', '2']))
        result = list(map(int, sp.get_user_choices(playlists)))
        self.assertEqual(result, expected_result)

    def test_spotifyToAppleMusicUsingISRC(self):

        client = SpotifyClient("testuser", transfer_all=False)
        tracks = pd.DataFrame({
            "track_ids": ["1", "2"],
            "track_titles": ["Track 1", "Track 2"],
            "track_first_artists": ["Artist 1", "Artist 2"],
            "track_popularity": [80, 90],
            "track_isrc": ["ISRC1", "ISRC2"],
        })
        with patch('applemusicpy.AppleMusic.songs_by_isrc', return_value={"data": []}):
            track_dataframe = client.spotifyToAppleMusicUsingISRC(tracks)

        self.assertEqual(len(track_dataframe), 0)

    def test_create_new_playlist(self):
        client = SpotifyClient("testuser", transfer_all=False)

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {"data": [{"id": "new_playlist_id"}]}
            result = client.create_new_playlist("Test Playlist")

        self.assertEqual(result, "new_playlist_id")

    def test_insert_track_to_playlist(self):
        client = SpotifyClient("testuser", transfer_all=False)

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 204
            result = client.insert_track_to_playlist("test_playlist_id", "test_track_id")

        self.assertTrue(result)

    # @patch('spotify_client.SpotifyClient.get_user_playlists_sp')
    # @patch('spotify_client.SpotifyClient.get_tracks_for_playlist')
    # @patch('spotify_client.SpotifyClient.spotifyToAppleMusicUsingISRC')
    # @patch('spotify_client.SpotifyClient.create_new_playlist')
    # @patch('spotify_client.SpotifyClient.insert_track_to_playlist')
    # def test_transfer_all_playlists_integration(self, mock_insert_track, mock_create_playlist, mock_spotify_to_apple_music, mock_get_tracks, mock_get_playlists):
        
    #     client = SpotifyClient("testuser", transfer_all=False)

    #     mock_get_playlists.return_value = pd.DataFrame({"playlist_id": ["playlist_1"], "playlist_name": ["Playlist 1"]})
    #     mock_get_tracks.return_value = pd.DataFrame(
    #         {
    #             "track_ids": ["1"],
    #             "track_titles": ["Track 1"],
    #             "track_first_artists": ["Artist 1"],
    #             "track_popularity": [80],
    #             "track_isrc": ["ISRC1"],
    #         }
    #     )
    #     mock_spotify_to_apple_music.return_value = pd.DataFrame({"track_name": ["Track 1"], "id": ["AM1"]})
    #     mock_create_playlist.return_value = 'new_playlist_id'
    #     mock_insert_track.return_value = True

    #     # Redirect stdout to capture print statements
    #     captured_output = StringIO()
    #     with redirect_stdout(captured_output):
    #         client.transfer_all_playlists(mock_get_playlists.return_value)

    #     output = captured_output.getvalue().split('\n')
    #     self.assertIn('Adding songs to playlist new_playlist_id', output)
    #     self.assertIn('Added track Track 1', output)
    #     self.assertIn('Here is a link to the apple music playlist created: https://music.apple.com/library/playlist/new_playlist_id', output)

if __name__ == "__main__":
    unittest.main()
