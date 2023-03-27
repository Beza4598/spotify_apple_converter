# Spotify to Apple Music Converter

This web app allows you to easily perform cross-platform playlist migration from spotify to apple-music and vice-versa.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

![GitHub issues](https://img.shields.io/github/issues-raw/Beza4598/spotify_apple_converter)

![Codecov](https://img.shields.io/codecov/c/github/Beza4598/spotify_apple_converter)

## Overview

The first version of this program will allow you to run on one mode --all to transfer all of your playlists from Spotify to Apple music. After cloning the repository to your local machine run `make develop` and `make install` to install the dependencies needed to run the program. Once the dependencies are installed run the program using the following CLI command `spotify_client -all <your_spotify_username>` and the program will first use the Spotipy api to find all of your current playlists on spotify and for each playlist it will go through each track to find an itunes identifier for the track using the track's ISRC, a unique identifier for any soundtrack that has been published publicly. For the songs it was able to match the program will make http POST request to copy each playlist over to apple music with 3 second interval before each insertion to bypass the rate limit apple places on API requests.

To run tests on the program you can use `make test`.

## Usage
- `make`: list available commands
- `make develop`: install and build this library and its dependencies using `pip`
- `make build`: build the library using `setuptools`
- `make lint`: perform static analysis of this library with `flake8` and `black`
- `make format`: autoformat this library using `black`
- `make test`: run automated tests with `pytest`
- `make coverage`: run automated tests with `pytest` and collect coverage information
- `make dist`: package library for distribution
