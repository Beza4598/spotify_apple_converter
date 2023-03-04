import unittest
from unittest import TestCase, mock
import pandas as pd
from unittest.mock import patch
from spotify_client import SpotifyClient


class TestSpotifyClient(unittest.TestCase):
    def test_get_user_info(self):
        spotify_client = SpotifyClient()

        mock_user = "bezamufc"
        with mock.patch("sys.stdin", f"{mock_user}"):
            self.assertEqual(spotify_client.get_user_info, mock_user)

    def test_get_user_playlists_sp(self):
        expected_df = pd.DataFrame(
            {
                "playlist_id": [
                    "3KURYmbLnaHDao8K1UMSfd",
                    "56vy9PiY0nnHDrXVTAMYnV",
                    "4OcepoXUKHPGBG3ljRVfgt",
                    "4gUoTNM8syGwJWl2WeVJSR",
                    "1gsDRtI4JojX5RedJcPLy3",
                    "3yG5QW5sVO5JthxSK83wNm",
                    "06V6xKV9flzaWUtiQCNEMU",
                    "49CIZOwvsiYvsjnxxbjA1J",
                    "2WtgL6glAYmskMA0VSBCug",
                    "37i9dQZF1DX7bxurrN0PHJ",
                    "5vj3ueGRO2pNpO0LjKDh4Y",
                    "4s8gQPiQ1pfR4GFQJZ14B5",
                    "6gIMCbaV5WOvg8fdPXmKN3",
                    "6oViDgZ5sh2VJ858bbTjef",
                    "3MTDK7pdPLtdvgBEUSD3gE",
                    "2icTFUbs9n7ywc0XhZm28k",
                    "0IW0JqIhbey9b6O3r5LrUr",
                    "37i9dQZF1DWTl4y3vgJOXW",
                    "4l5ABfDp5EQMAeCSCYKdiv",
                    "2rcRZu2uqw3uITy5BuRNoH",
                    "0FM69fPKPRquWibaJmRhqd",
                    "6HZ4lXRo3j5UWqKijOKBCE",
                    "0HVTFdS6tPZFcoQqbFVFy8",
                    "7n56gFBLt6tUCHy9x8lGGq",
                    "7oNUVOArrPzQHfYvhK0i5S",
                ],
                "playlist_name": [
                    "My Playlist #11",
                    "Fikratchin",
                    "Ethiopian classics",
                    "My Playlist #8",
                    "Off the Wall: American Art to Wear",
                    "Friday Night in Your Living Room",
                    "Elegy: Lament in the 20th Century",
                    "Head in the Clouds: Ethiopian Soul",
                    "Flow State: Ethiopian Jazz & Instrumental",
                    "Grime Classics",
                    "GYM hype",
                    "EESA CU",
                    "for uma & beza & nish",
                    "Sad Boi Hour Shower 🧼",
                    "HSN",
                    "Ampiano Mix 🇿🇦",
                    "GRIDDY 🧪💉",
                    "Locked In",
                    ".",
                    "Saxophone Faves🎷",
                    ".eth",
                    "OYINBO SOUL",
                    "Gym Carti 🧛🏽",
                    "Chill",
                    "Ethiopiques + Others",
                ],
            }
        )

        with patch("builtins.input", return_value="test_user"), patch.object(
            self.spotify_client, "_generate_token", return_value="test_token"
        ), patch(
            "spotipy.Spotify.current_user_playlists",
            return_value={
                "items": [
                    {"id": "playlist_id_1", "name": "playlist_name_1"},
                    {"id": "playlist_id_2", "name": "playlist_name_2"},
                ]
            },
        ):
            self.assertEqual(
                self.spotify_client.get_user_playlists_sp().to_dict(),
                expected_df.to_dict(),
            )

    def test_get_user_choices(self):
        with patch("builtins.input", side_effect=["S", "1,2"]):
            self.assertEqual(
                self.spotify_client.get_user_choices(
                    ["playlist_1", "playlist_2", "playlist_3"]
                ),
                [1, 2],
            )

        with patch("builtins.input", return_value="A"):
            self.assertEqual(
                self.spotify_client.get_user_choices(
                    ["playlist_1", "playlist_2", "playlist_3"]
                ),
                [0, 1, 2],
            )

    def test_get_tracks_for_playlist(self):
        expected_df = pd.DataFrame(
            {
                "track_ids": [
                    "5nggPkwWmLbqUCCaUfDPjZ",
                    "6a8q9ysqdMzac7NbXyXTks",
                    "4Lx2aLc9JltrvNFSTrcuNY",
                    "4t6uFxnuY7bcxi83P2x8pg",
                    "37S24CU10wU5lY8wTB76Qm",
                    "2OzsgjI3O8SkFF1pjGX7gz",
                    "5ynFflAdInWSaqVXzXQ8Iu",
                    "2rwx7G5IxAuw2PopvFupl2",
                    "4F43An0aEAZurV33HKuPlN",
                    "7uathmF6Dhe269Z79w1LTN",
                    "7FTywuxqZm5nFhoZGP0xn2",
                    "1ndWXkJUryhxsTjyMWL58l",
                    "5tROTH4zGtjFPlLZU11aam",
                    "36HX8yDViP2Q8ODyhinFX0",
                    "3p2TK4IMUPnbbD7RBtqLu1",
                    "5nUbqoz7j9btdIZkkuJL5a",
                    "49JzCnLzparJQ2Sfs7gU5C",
                    "4iKrEZyjF2JcC5AukB2rBF",
                    "3BxMUw1RudApjSG9emnP5K",
                    "0Dt1QXrt51L77fXJhCy1Hj",
                    "2IMHkEePPt8hNKnnNZMIQv",
                    "38FO12pCWu4PGGlCepCk8B",
                ],
                "track_titles": [
                    "Selame",
                    "Bewene",
                    "Gunfan",
                    "Habesha",
                    "Amelework",
                    "Eighteen Eighty Eight",
                    "Bado",
                    "Chiggae",
                    "Bado Neber",
                    "Qalen",
                    "Tefa Yemileyen",
                    "123",
                    "Sakesh Yigodal",
                    "Berta",
                    "Helm",
                    "Debzezesh",
                    "Nekchalehu",
                    "Kenat Wediya",
                    "Keteraraw Mado",
                    "Mela Mela",
                    "Sewasew",
                    "Yehagere Lij",
                ],
                "track_first_artists": [
                    "micsolo",
                    "micsolo",
                    "micsolo",
                    "micsolo",
                    "Kassmasse",
                    "Kassmasse",
                    "Nhatty Man",
                    "Haile Roots",
                    "Haile Roots",
                    "Sami Dan",
                    "Sami Dan",
                    "Sami Dan",
                    "Yohana",
                    "Yohana",
                    "Yohana",
                    "Eyob Mekonen",
                    "Eyob Mekonen",
                    "Jano Band",
                    "Jano Band",
                    "Kassmasse",
                    "Kassmasse",
                    "Kassmasse",
                ],
                "track_popularity": [
                    0,
                    0,
                    0,
                    0,
                    18,
                    14,
                    21,
                    28,
                    18,
                    27,
                    29,
                    31,
                    0,
                    1,
                    0,
                    29,
                    34,
                    14,
                    26,
                    20,
                    24,
                    21,
                ],
                "track_isrc": [
                    "QZPYN2117995",
                    "QZPYN2117998",
                    "QZPYN2117996",
                    "QZPYN2117997",
                    "TCAFM2131413",
                    "TCAFM2131498",
                    "usl4q1729169",
                    "uscgj1212684",
                    "uscgj1212683",
                    "QZMEN2147439",
                    "uscgj1684158",
                    "usdy41939230",
                    "QZPYN2112222",
                    "QZPYN2112223",
                    "ZA56E1900036",
                    "FR10S1631455",
                    "FR10S1631450",
                    "uscgh1861525",
                    "uscgh1861518",
                    "TCAGB2244233",
                    "TCAGB2244256",
                    "TCAGB2244247",
                ],
            }
        )

        mock_playlist_id = "0FM69fPKPRquWibaJmRhqd"
        with patch("builtins.input", return_value="test_user"), patch.object(
            self.spotify_client, "_generate_token", return_value="test_token"
        ), patch(
            "spotipy.Spotify.user_playlist_tracks",
            return_value={
                "items": [
                    {
                        "track": {
                            "id": "track_id_1",
                            "name": "track_title_1",
                            "popularity": 1,
                            "external_ids": {"isrc": "track_isrc_1"},
                            "artists": [{"name": "track_artist_1"}],
                        }
                    },
                    {
                        "track": {
                            "id": "track_id_2",
                            "name": "track_title_2",
                            "popularity": 2,
                            "external_ids": {"isrc": "track_isrc_2"},
                            "artists": [{"name": "track_artist_2"}],
                        }
                    },
                ]
            },
        ):
            self.assertEqual(
                self.spotify_client.get_tracks_for_playlist(mock_playlist_id).to_dict(),
                expected_df.to_dict(),
            )
