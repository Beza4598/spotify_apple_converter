Spotify to Apple Music Converter
================================

.. include:: ../README.md
   :parser: myst_parser.sphinx_
   :start-after: <!-- docs-start -->

API reference
-------------

.. autoclass:: spotify_to_apple.SpotifyClient
   :members: list_playlists, transfer_single_playlist, transfer_all_playlists

.. autoclass:: spotify_to_apple.TransferResult
   :members:

.. autoclass:: spotify_to_apple.Track

.. autoclass:: spotify_to_apple.Playlist

.. autoclass:: spotify_to_apple.Credentials
   :members: from_env

.. autoclass:: spotify_to_apple.AppleMusicClient
   :members: storefront, songs_by_isrc, create_playlist, add_tracks

.. autofunction:: spotify_to_apple.parse_playlist_id

.. automodule:: spotify_to_apple.errors
   :members:
