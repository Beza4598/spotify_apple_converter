## Contributing

If you would like to contribute to spotipy follow these steps:

### Set the neccessary environment variables

```bash
client_id = "x"
client_secret = "y"
callback_address = "z" #make sure this is set as the callback adress in the spotify web-api dashboard
```

```bash
secret_key = 'x'
key_id = 'y'
team_id = 'z'
```

### Create virtual environment, install dependencies, run tests:

```bash
$ virtualenv --python=python3 env
$ source env/bin/activate
(env) $ make develop
(env) $ make build

```

### Lint

To automatically fix the code style and verify the code style:

    make lint





