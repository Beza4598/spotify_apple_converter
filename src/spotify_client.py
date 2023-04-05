import spotipy
import pandas as pd
import applemusicpy
import requests
import json
from datetime import datetime, timedelta
import jwt
from spotipy.oauth2 import CacheFileHandler
from dotenv import load_dotenv
import os

load_dotenv()


key_id = os.environ.get("APPLE_KEY_ID")
team_id = os.environ.get("APPLE_TEAM_ID")
music_user_token = os.environ.get("APPLE_USER_TOKEN")
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
callback_address = os.environ.get("CALLBACK_ADDRESS")


class SpotifyClient:
    """
    A class to transfer playlists from Spotify to Apple Music.

    Attributes:
        user (str): Spotify username.
        transfer_all (bool): Determines if all playlists should be transferred. Defaults to True.
        path (str): File path for user's Apple developer token stored in a .p8 file.

    Methods:
        transfer_all(): Initiates the process of transferring all playlists from Spotify to Apple Music.
        transfer_single_playlist(playlist_url, playlist_name="New Playlist"): Transfers a single playlist
        from Spotify to Apple Music.
    """

    def __init__(self, user, path, transfer_all=True, auth_manager=None):
        with open(path, 'r') as f:
            self.secret_key = f.read()

        self.user = user
        self.transfer_all = transfer_all
        self.music_user_token = music_user_token
        self.developer_token = ''
        self.am = applemusicpy.AppleMusic(secret_key=self.secret_key, key_id=key_id, team_id=team_id)
        self._alg = 'ES256'
        self._generate_am_token(12)
        self.auth_manager = auth_manager

    def get_user_info(self):
        username = input("Please enter your spotify username: ")
        self.user = username

        return username

    def _generate_am_token(self, session_length):
        token_exp_time = datetime.now() + timedelta(hours=session_length)
        headers = {'alg': self._alg, 'kid': key_id}
        payload = {
            'iss': team_id,
            'iat': int(datetime.now().timestamp()),  # issued at
            'exp': int(token_exp_time.timestamp()),  # expiration time
        }
        self.token_valid_until = token_exp_time
        token = jwt.encode(payload, self.secret_key, algorithm=self._alg, headers=headers)
        self.developer_token = token if type(token) is not bytes else token.decode()

    def _generate_token(self, scope):
        if self.auth_manager is None:
            cache_handler = CacheFileHandler(cache_path=f".cache-{self.user}", username=self.user)
            self.auth_manager = spotipy.SpotifyOAuth(
                client_id, client_secret, callback_address, scope=scope, cache_handler=cache_handler
            )

        token_info = self.auth_manager.validate_token(self.auth_manager.cache_handler.get_cached_token())
        if not token_info:
            auth_url = self.auth_manager.get_authorize_url()
            print(f"Please navigate here: {auth_url}")
            response = input("Enter the URL you were redirected to: ")
            code = self.auth_manager.parse_response_code(response)
            token_info = self.auth_manager.get_access_token(code)

        return token_info["access_token"]

    def get_user_playlists_sp(self):
        playlist_name = []
        playlist_id = []

        scope = "user-library-read"
        token = self._generate_token(scope)

        if token:
            sp = spotipy.Spotify(auth=token)
            playlists = sp.current_user_playlists()

            for playlist in playlists["items"]:
                playlist_name.append(playlist["name"])
                playlist_id.append(playlist["id"])

            playlist_df = pd.DataFrame({"playlist_id": playlist_id, "playlist_name": playlist_name})

        else:
            print(f"Unable to generate token for {self.user}")
            playlist_df = None

        return playlist_df

    def get_user_choices(self, playlists):
        if not self.transfer_all:
            u_choice = input(
                "Please enter the numbers associated\
                 with the playlists you want to transfer\
                separated by commas."
            )
            u_choice = u_choice.strip().split(",")
        if self.transfer_all:
            u_choice = list(range(0, len(playlists)))

        return u_choice

    def get_tracks_for_playlist(self, playlist_id):
        scope = "user-library-read"
        token = self._generate_token(scope)

        track_ids = []
        track_titles = []
        track_first_artists = []
        track_popularity = []
        track_isrc = []

        if token:
            sp = spotipy.Spotify(auth=token)
            results = sp.user_playlist_tracks(self.user, playlist_id)
            tracks = results["items"]

            # avoiding the limit because of paginated results
            # produced by the api thus we're scrolling through
            # the data to ensure every track is returned
            while results["next"]:
                results = sp.next(results)
                tracks.extend(results["items"])

            results = tracks

            for track in results:
                track = track["track"]
                track_ids.append(track["id"])
                track_titles.append(track["name"])
                track_first_artists.append(track["artists"][0]["name"])
                track_popularity.append(track["popularity"])
                track_isrc.append(track["external_ids"]["isrc"])

            track_df = pd.DataFrame(
                {
                    "track_ids": track_ids,
                    "track_titles": track_titles,
                    "track_first_artists": track_first_artists,
                    "track_popularity": track_popularity,
                    "track_isrc": track_isrc,
                }
            )

        else:
            print(f"Unable to generate token for {self.user}")
            track_df = None

        return track_df

    def spotifyToAppleMusicUsingISRC(self, tracks):
        track_names = []
        track_ids = []

        for ind in tracks.index:
            track_result = self.am.songs_by_isrc([tracks["track_isrc"][ind]])
            if not len(track_result["data"]) == 0:
                am_id = track_result["data"][0]["id"]
                track_name = track_result["data"][0]["attributes"]["name"]
                track_names.append(track_name)
                track_ids.append(am_id)

        track_dataframe = pd.DataFrame(
            {
                "track_name": track_names,
                "id": track_ids,
            }
        )

        return track_dataframe

    def create_new_playlist(self, name):
        playlist_data = {"attributes": {"name": name, "description": "Playlist transfered by program."}}

        response = requests.post(
            "https://api.music.apple.com/v1/me/library/playlists",
            data=json.dumps(playlist_data),
            headers={'Authorization': 'Bearer %s' % self.developer_token, 'Music-User-Token': self.music_user_token},
        )

        if response.status_code == 201:
            return response.json()['data'][0]['id']
        if response.status_code == 401:
            return 'Unauthorized'
        if response.status_code == 403:
            return 'Forbidden'

    def insert_track_to_playlist(self, playlist_id, track_id):
        url = "https://api.music.apple.com/v1/me/library/playlists/%s/tracks" % playlist_id

        song_data = {"data": [{"id": track_id, "type": "songs"}]}

        response = requests.post(
            url,
            data=json.dumps(song_data),
            headers={'Authorization': 'Bearer %s' % self.developer_token, 'Music-User-Token': self.music_user_token},
        )

        if response.status_code == 204:
            return True

        return False

    def transfer_all_playlists(self, playlist_dataframe_sp):
        for ind in playlist_dataframe_sp.index:
            tracks = self.get_tracks_for_playlist(playlist_dataframe_sp["playlist_id"][ind])
            apple_music_identifiers = self.spotifyToAppleMusicUsingISRC(tracks)

            am_playlist_id = self.create_new_playlist(playlist_dataframe_sp["playlist_name"][ind])

            print(f"\nAdding songs to playlist {am_playlist_id}")

            for ind in apple_music_identifiers.index:
                track_name = apple_music_identifiers["track_name"][ind]
                if self.insert_track_to_playlist(am_playlist_id, apple_music_identifiers["id"][ind]):
                    print(f"Added track {track_name}")
                else:
                    print(f"Unable to add track {track_name}")

            print("\n")
            url = 'https://music.apple.com/library/playlist/' + am_playlist_id
            print("Here is a link to the apple music playlist created: " + url)

    def transfer_single_playlist(self, playlist_url, playlist_name="New Playlist"):
        """
        Transfers a single playlist from Spotify to Apple Music.

        Args:
            playlist_url (str): The URL of the Spotify playlist to be transferred.
            playlist_name (str, optional): The name for the new Apple Music playlist. Defaults to "New Playlist".

        This function performs the following steps:
            1. Extracts the playlist ID from the given Spotify playlist URL.
            2. Retrieves the tracks for the playlist.
            3. Converts the tracks to Apple Music format using their ISRC.
            4. Creates a new playlist on Apple Music with the given name.
            5. Inserts the converted tracks to the new Apple Music playlist and prints their status.
            6. Prints the URL of the newly created Apple Music playlist.
        """

        id = self.get_playlist_id(playlist_url)
        tracks = self.get_tracks_for_playlist(id)

        apple_music_identifiers = self.spotifyToAppleMusicUsingISRC(tracks)

        am_playlist_id = self.create_new_playlist(playlist_name)

        print(f"\nAdding songs to playlist {am_playlist_id}")

        for ind in apple_music_identifiers.index:
            track_name = apple_music_identifiers["track_name"][ind]
            if self.insert_track_to_playlist(am_playlist_id, apple_music_identifiers["id"][ind]):
                print(f"Added track {track_name}")
            else:
                print(f"Unable to add track {track_name}")

            print("\n")
            url = 'https://music.apple.com/library/playlist/' + am_playlist_id
            print("Here is a link to the apple music playlist created: " + url)

    def transfer_all(self):
        """
        Initiates the process of transferring playlists.

        Retrieves all of the user's playlists from Spotify and transfers each playlist to Apple Music.
        """

        playlists = self.get_user_playlists_sp()
        self.transfer_all_playlists(playlists)
