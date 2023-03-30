## Contributing Guidelines
### Overview
This program provides a convenient way to transfer all of your playlists from Spotify to Apple Music. The initial version supports the --all mode to transfer all playlists at once. Before running the program, you need to configure the necessary API keys and tokens in the config.py file located in the src folder.

### Apple Music API Configuration
To make requests to the Apple Music API, you need several keys, which can be obtained by enrolling in the Apple Developer Program. Once enrolled, you can access your team_id, secret_key, and key_id directly. However, generating a music_user_token requires extra steps since the Apple user authorization service is not available in Python. We recommend following the instructions in this GitHub repository to generate your music_user_token. Once you have all of the required information, first replace the apple_private_key.p8 file with your private_key.p8 file that you downloaded from Apple. Then create a .env file in the src folder and set these variables to their corresponding values.

```
# Apple API configuration
APPLE_KEY_ID=""
APPLE_TEAM_ID=""
APPLE_USER_TOKEN=""
```

### Spotify API Configuration
Obtaining the Spotify API keys is more straightforward. After logging in to the Spotify Web API Dashboard with your Spotify account, you will have access to the required keys. Add them to the corresponding variables in the .env file you just created.

```
Spotify API configuration
CLIENT_ID=""
CLIENT_SECRET=""
CALLBACK_ADDRESS=""
```

The program uses the Spotipy API to retrieve your current Spotify playlists and iterates through each track to find an iTunes identifier using the track's ISRC (a unique identifier for any published soundtrack). For matched songs, the program sends HTTP POST requests to copy each playlist to Apple Music. To comply with Apple's rate limit on API requests, there is a 3-second interval between each insertion.

To run tests on the program, use make test. We welcome contributions to improve the program and its documentation. Please follow the guidelines below when contributing.

## Contribution Guidelines
* Before creating a pull request, please ensure that the tests pass by running make test.
* Use clear and concise language when adding to or modifying the documentation.
* When adding a new feature or modifying existing code, please include tests to ensure that the code works as expected.
* Follow PEP 8 style guide for Python code.
