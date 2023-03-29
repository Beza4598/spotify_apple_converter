# Spotify to Apple Music Converter

This web app allows you to easily perform cross-platform playlist migration from spotify to apple-music and vice-versa.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

![GitHub issues](https://img.shields.io/github/issues-raw/Beza4598/spotify_apple_converter)

![Codecov](https://img.shields.io/codecov/c/github/Beza4598/spotify_apple_converter)

[![Build Status](https://github.com/Beza4598/spotify_apple_converter/workflows/Build%20Status/badge.svg?branch=main)](https://github.com/Beza4598/spotify_apple_converter/actions?query=workflow%3A%22Build+Status%22)

![Build Status](https://img.shields.io/github/actions/workflow/status/Beza4598/spotify_apple_converter/workflow.yml)

## Overview

This program provides a convenient way to transfer all of your playlists from Spotify to Apple Music. The initial version supports the `--all` mode to transfer all playlists at once. Before running the program, you need to configure the necessary API keys and tokens in the `config.py` file located in the `src` folder.

### Apple Music API Configuration

To make requests to the Apple Music API, you need several keys, which can be obtained by enrolling in the Apple Developer Program. Once enrolled, you can access your `team_id`, `secret_key`, and `key_id` directly. However, generating a `music_user_token` requires extra steps since the Apple user authorization service is not available in Python. We recommend following the instructions in this [GitHub repository](https://github.com/KoleMyers/apple-musickit-example) to generate your `music_user_token`.

```
# Apple API configuration
secret_key = ""
key_id = ""
team_id = ""
music_user_token = ""
```

### Spotify API Configuration

Obtaining the Spotify API keys is more straightforward. After logging in to the Spotify Web API Dashboard with your Spotify account, you will have access to the required keys. Add them to the corresponding variables in the config.py file.

```
# Spotify API configuration
client_id = ""
client_secret = ""
callback_address = ""
```

The program uses the Spotipy API to retrieve your current Spotify playlists and iterates through each track to find an iTunes identifier using the track's ISRC (a unique identifier for any published soundtrack). For matched songs, the program sends HTTP POST requests to copy each playlist to Apple Music. To comply with Apple's rate limit on API requests, there is a 3-second interval between each insertion.

Run tests on the program using make test.




## Usage
- `make`: list available commands
- `make develop`: install and build this library and its dependencies using `pip`
- `make build`: build the library using `setuptools`
- `make lint`: perform static analysis of this library with `flake8` and `black`
- `make format`: autoformat this library using `black`
- `make test`: run automated tests with `pytest`
- `make coverage`: run automated tests with `pytest` and collect coverage information
- `make dist`: package library for distribution
