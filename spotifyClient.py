import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

class SpotifyClient:

    def __init__(self, credentials):
        self.credentials = credentials
        self.sp = spotipy.Spotify(client_credentials_manager = credentials)
        self._isPlaylistLoading = False
        self.playlistData = []
        self.token = self._generateToken()
        self.spotify = spotipy.Spotify(auth=self.token)

        PLAYLIST_LIMIT = 50
        SEARCH_LIMIT = 20

    #generates token for user authentication
    def _generateToken(self):
        token = self.credentials.get_access_token()
        return token

    #finds all the playlists for a particular user
    def loadAllPlaylists(self):
        playlists = self.sp.user_playlists('spotify')
        result = []
        while playlists:
            for i, playlist in enumerate(playlists['items']):
                result.append({'id' : playlist['uri'].split(':')[2], 'title':  playlist['name']})
            if playlists['next']:
                playlists = self.sp.next(playlists)
            else:
                playlists = None

        return result

    def findItunesTrackIdentifier(self, track):
    
        title = track['title']


        return results['tracks']
    
    def findAllTracks(self, playlist_id):
        result = []


    def findAppleIdentifier(title, artist):
        pass


if __name__ == "__main__":
    cid = '90cc35748b224a06b666072fe72b93e1'
    secret = 'bbc13812e4644d5ab904f6d32001fcaf'

    client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
    sp = spotipy.Spotify(client_credentials_manager =client_credentials_manager)
    playlistFetcher = SpotifyClient(client_credentials_manager)
    print(playlistFetcher.loadAllPlaylists())
