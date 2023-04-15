# Spotify to Apple Music Converter

This web app allows you to easily perform cross-platform playlist migration from spotify to apple-music and vice-versa.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![GitHub issues](https://img.shields.io/github/issues-raw/Beza4598/spotify_apple_converter)
![Codecov](https://img.shields.io/codecov/c/github/Beza4598/spotify_apple_converter)
[![Build Status](https://github.com/Beza4598/spotify_apple_converter/workflows/Build%20Status/badge.svg?branch=main)](https://github.com/Beza4598/spotify_apple_converter/actions?query=workflow%3A%22Build+Status%22)
![PyPI](https://img.shields.io/pypi/v/spotify-to-apple-py)

[Documentation](https://spotify-apple-converter.readthedocs.io/en/latest/)
## Overview

This program provides a convenient way to transfer all of your playlists from Spotify to Apple Music. Before running the program, you need to configure the necessary API keys and tokens.

You can install this python library using:

`pip install spotify-to-apple-py`

### Apple Music API Configuration

To make requests to the Apple Music API, you need several keys, which can be obtained by enrolling in the Apple Developer Program. Once enrolled, you can access your `team_id`, `secret_key`, and `key_id` directly. However, generating a `music_user_token` requires extra steps since the Apple user authorization service is not available in Python. We recommend following the instructions in this [GitHub repository](https://github.com/KoleMyers/apple-musickit-example) to generate your `music_user_token`. Once you have all of the required information, first replace the apple_private_key.p8 file with your `private_key.p8` file that you downloaded from Apple. then create a `.env` file and set these variables to their corresponding values or export it from your cli.

```
# Apple API configuration
export APPLE_KEY_ID=""
export APPLE_TEAM_ID=""
export APPLE_USER_TOKEN=""
```

### Spotify API Configuration

Obtaining the Spotify API keys is more straightforward. After logging in to the Spotify Web API Dashboard with your Spotify account, you will have access to the required keys. Add them to the corresponding variables in the .env file you just created.

```
# Spotify API configuration
export CLIENT_ID=""
export CLIENT_SECRET=""
export CALLBACK_ADDRESS=""

```

Once you have set these enviroment variables you need to download the .p8 file for your apple developer key and you can instantiate the client as follows:

`from spotify_client import SpotifyClient`

```
path = "/path to your .p8 file"
sp = SpotifyClient("<your spotify username>", path)

sp.transfer_all_playlists() #to transfer all of your playlists from spotify to apple music

sp.transfer_single_playlist(<spotify_playlist_url>, <name_of_the_playlist>) #to transfer a single playlist from spotify to apple music

```



The program uses the Spotipy API to retrieve your current Spotify playlists and iterates through each track to find an iTunes identifier using the track's ISRC (a unique identifier for any published soundtrack). For matched songs, the program sends HTTP POST requests to copy each playlist to Apple Music. To comply with Apple's rate limit on API requests, there is a 3-second interval between each insertion.


Run tests on the program using make test.


Once up and running the program should update you on the progress of conversion as shown below. And pres cmd and click on the link to go to the playlist.

### Demo

## Transfer all of your playlists from Spotify to Apple Music

![transfer-all](https://github.com/Beza4598/spotify_apple_converter/blob/main/docs/transfer-all.gif)

## Transfer a particular playlist from Spotify to Apple Msuic using playlist url

![transfer-single](https://github.com/Beza4598/spotify_apple_converter/blob/main/docs/transfer-single.gif)


## Starter Code
```

   #Export a single playlist 

   from spotify_client import SpotifyClient

   username = "bezamufc"
   secret_key_path = "Untitled/Users/bezaamsalu/Desktop/apple_private_key.py"

   sp = SpotifyClient(username, secret_key_path)

   ## transfer a single playlist

   playlist_url = "https://open.spotify.com/playlist/5p1MWp58nGHAryTnJdmFCb?si=ed9f8a32d1534cb4"
   sp.transfer_single_playlist(playlist_url, "African Soul")
```
This is the console output when running the following code.

```
   Adding songs to playlist p.QvDQBYMI76rbqNe

   Added track Ali Farka
   Added track DéFaal Lu Wor (Once In A Lifetime)
   Added track Everything (... Is Never Quite Enough) Added track Anna Mou
   Added track Niko Sawa (feat. Bien)
   Added track Mali Men
   Added track Fala
   Added track Ba Kristo
   Added track Greetings from the Colony
   Added track Alteleyeshegnem
   Added track Temar Ledje
   Added track Alègntayé (feat. Genet Asefa)
   Added track Enkèn Yèlélèbesh

   Here is a link to the apple music playlist created: https://music.apple.com/library/playlist/p.QvDQBYMI76rbqNe
```


## Usage
- `make`: list available commands
- `make develop`: install and build this library and its dependencies using `pip`
- `make build`: build the library using `setuptools`
- `make lint`: perform static analysis of this library with `flake8` and `black`
- `make format`: autoformat this library using `black`
- `make test`: run automated tests with `pytest`
- `make coverage`: run automated tests with `pytest` and collect coverage information
- `make dist`: package library for distribution
