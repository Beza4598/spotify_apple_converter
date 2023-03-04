import sys
import spotipy
import spotipy.util as util
import val
import pandas as pd


class SpotifyClient:
    def __init__(self):
        self.user = "bezamufc"
        # self.am = applemusicpy.AppleMusic(val.secret_key, val.key_id, val.team_id)

    def get_user_info(self):
        username = input("Please enter your spotify username: ")
        self.user = username

        return username

    def _generate_token(self, scope):
        token = util.prompt_for_user_token(
            self.user, scope, val.client_id, val.client_secret, val.callback_address
        )
        return token

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

            playlist_df = pd.DataFrame(
                {"playlist_id": playlist_id, "playlist_name": playlist_name}
            )

            print(playlist_df)

        else:
            print(f"Unable to generate token for {self.user}")

        return playlist_df

    def get_user_choices(self, playlists):
        selection = input("Transfer (A)ll playlists or (S)elect playlists? ")

        if selection == "S":
            u_choice = input(
                "Please enter the numbers associated with the playlists you want to transfer separated by commas"
            )
            u_choice = u_choice.trim().split(",")
        if selection == "A":
            u_choice = list(range(0, len(playlists)))
        else:
            print("Invalid input. System exiting ...")
            sys.exit()

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

            # avoiding the limit because of paginated results produced by the api
            # thus we're scrolling through the data to ensure every track is returned
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

        track_dataframe22 = pd.DataFrame(
            {
                "artist_name": artist_name,
                "track_name": track_name,
                "release_date": date_added,
                "id": track_id,
            }
        )

        print(track_dataframe22)

    def matchByISRC(self, tracks):
        pass


if __name__ == "__main__":
    playlistFetcher = SpotifyClient()
    result = playlistFetcher.get_tracks_for_playlist("0FM69fPKPRquWibaJmRhqd")[
        "track_ids"
    ].to_list()
    print(result)
