import spotipy
import pandas as pd
import applemusicpy
import spotipy.util as util
import requests
import json
import time
import sys

# sample keys until I get access to Apple Developer program
secret_key = 'x'
key_id = 'y'
team_id = 'z'

client_id = "90cc35748b224a06b666072fe72b93e1"
client_secret = "bbc13812e4644d5ab904f6d32001fcaf"
callback_address = "http://localhost:8888/callback/"


class SpotifyClient:
    def __init__(self, user, transfer_all=True):
        self.user = user
        self.transfer_all = transfer_all
        self.am = applemusicpy.AppleMusic(secret_key=secret_key, key_id=key_id, team_id=team_id)
        self.am_user_token = ''
        self.am_developer_token = ''

    def get_user_info(self):
        username = input("Please enter your spotify username: ")
        self.user = username

        return username

    def _generate_token(self, scope):
        token = util.prompt_for_user_token(self.user, scope, client_id, client_secret, callback_address)
        return token

    def get_user_playlists_sp(self):
        playlist_name = []
        playlist_id = []

        scope = "user-library-read"
        token = self._generate_token(scope)

        if token:
            sp = spotipy.Spotify(auth=token)
            playlists = sp.current_user_playlists()

            print(playlists)

            for playlist in playlists["items"]:
                playlist_name.append(playlist["name"])
                playlist_id.append(playlist["id"])

            playlist_df = pd.DataFrame({"playlist_id": playlist_id, "playlist_name": playlist_name})

            print(playlist_df)

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

    def spotifyPlaylistToApple(self, tracks):
        artist_name = []
        track_name = []
        date_added = []
        track_id = []

        for track in tracks:
            track_result = self.am.search(track["track_name"], types=["songs"], limit=1)
            var = track_result["results"]["songs"]["data"][0]["attributes"]
            artist_name.append(var["artistName"])
            track_name.append(var["name"])
            date_added.append(var["releaseDate"])
            track_id.append(var["playParams"]["id"])

        track_dataframe = pd.DataFrame(
            {
                "artist_name": artist_name,
                "track_name": track_name,
                "release_date": date_added,
                "id": track_id,
            }
        )

        return track_dataframe


# commented out until I get developer tokens from Apple Developer program

# def spotifyToAppleMusicUsingISRC(self, tracks):
#     track_names = []
#     track_ids = []

#     for track in tracks:
#         track_result = self.am.songs_by_isrc([track["track_isrc"]])
#         am_id = track_result[0]["attributes"]["id"]
#         track_name = track_result[0]["attributes"]["name"]
#         track_names.append(track_name)
#         track_ids.append(am_id)

#     track_dataframe = pd.DataFrame(
#         {
#             "track_name": track_names,
#             "id": track_ids,
#         }
#     )

#     return track_dataframe

# def create_new_playlist(name):
#     playlist_data = {
#                     "attributes":
#                      {"name": name,
#                       "description": "Playlist transfered by program."}
#                         }

#     response = requests.post(
#         "https://api.music.apple.com/v1/me/library/playlists",
#         data=json.dumps(playlist_data),
#         headers={'Authorization': 'Bearer %s' % developer_token, 'Music-User-Token': music_user_token},
#     )

#     if response.status_code == 201:
#         return response.json()['data'][0]['id']

# def insert_track_to_playlist(self, playlist_id, track_id):
#     url = "https://api.music.apple.com/v1/me/library/playlists/%s/tracks" % playlist_id

#     song_data = {"data": [{"id": track_id, "type": "songs"}]}

#     response = requests.post(
#         url,
#         data=json.dumps(song_data),
#         headers={'Authorization': 'Bearer %s' % self.am_developer_token,
#                  'Music-User-Token': self.am_user_token},
#     )

#     if response.status_code == 201:
#         return True

#     return False

# def transfer_all_playlists(self, playlist_dataframe_sp):
#     for ind in playlist_dataframe_sp.index:
#         tracks = self.get_tracks_for_playlist(playlist_dataframe_sp["id"][ind])
#         apple_music_identifiers = self.spotifyToAppleMusicUsingISRC(tracks)

#         am_playlist_id = self.create_new_playlist(playlist_dataframe_sp["name"][ind])

#         print(f"#### Adding songs to playlist {am_playlist_id}")
#         for id in apple_music_identifiers:
#             if self.insert_track_to_playlist(am_playlist_id, id):
#                 print(f"Added track {id}")
#             else:
#                 print(f"Unable to add track {id}")

#             time.sleep(2)


def main():
    args = sys.argv

    if len(sys.argv) < 2:
        print("Usage: spotify_client <mode>")
        sys.exit(1)

    mode = sys.argv[1]

    # transfer all playlists
    if mode == "-all":
        if len(sys.argv) != 3:
            print("Usage: spotify_client -all <spotify_username>")
            sys.exit(1)

    user_name = sys.argv[2]
    client = SpotifyClient(user_name)
    playlists = client.get_user_playlists_sp()
    client.transfer_all_playlists(playlists)


if __name__ == "__main__":
    main()
