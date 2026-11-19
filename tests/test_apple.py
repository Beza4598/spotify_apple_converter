import json

import jwt
import pytest
import responses
from responses import matchers

from spotify_to_apple import AppleMusicClient, AppleMusicError
from spotify_to_apple.apple import API_ROOT

SONGS_URL = f"{API_ROOT}/catalog/us/songs"
PLAYLISTS_URL = f"{API_ROOT}/me/library/playlists"
TRACKS_URL = f"{PLAYLISTS_URL}/p.123/tracks"


def _song(song_id, isrc):
    return {"id": song_id, "type": "songs", "attributes": {"isrc": isrc}}


def _sent_ids(call):
    return [item["id"] for item in json.loads(call.request.body)["data"]]


def test_developer_token_is_signed_with_the_key(apple, ec_key):
    token = apple.developer_token

    claims = jwt.decode(token, ec_key[1], algorithms=["ES256"])
    assert claims["iss"] == "TEAM123"
    assert claims["exp"] - claims["iat"] == 12 * 3600
    assert jwt.get_unverified_header(token)["kid"] == "KEY123"


def test_developer_token_is_reused_until_close_to_expiry(apple, monkeypatch):
    now = [1_000_000.0]
    monkeypatch.setattr("spotify_to_apple.apple.time.time", lambda: now[0])
    first = apple.developer_token

    now[0] += 11 * 3600
    assert apple.developer_token == first

    now[0] += 3600
    assert apple.developer_token != first


@responses.activate
def test_requests_send_both_tokens(apple):
    responses.get(SONGS_URL, json={"data": []})

    apple.songs_by_isrc(["AB1"])

    headers = responses.calls[0].request.headers
    assert headers["Authorization"] == f"Bearer {apple.developer_token}"
    assert headers["Music-User-Token"] == "user-token"


@responses.activate
def test_songs_by_isrc_batches_dedupes_and_normalises(apple):
    isrcs = [f"isrc{n:03d}" for n in range(30)] + ["ISRC000", "", None]
    first = [f"ISRC{n:03d}" for n in range(25)]
    second = [f"ISRC{n:03d}" for n in range(25, 30)]
    responses.get(
        SONGS_URL,
        match=[matchers.query_param_matcher({"filter[isrc]": ",".join(first)})],
        json={"data": [_song("100", "ISRC000"), _song("999", "OTHER")]},
    )
    responses.get(
        SONGS_URL,
        match=[matchers.query_param_matcher({"filter[isrc]": ",".join(second)})],
        json={"data": [], "meta": {"filters": {"isrc": {"isrc029": [{"id": "129"}], "ISRC028": []}}}},
    )

    assert apple.songs_by_isrc(isrcs) == {"ISRC000": "100", "ISRC029": "129"}
    assert len(responses.calls) == 2


@responses.activate
def test_songs_by_isrc_treats_404_as_no_match(apple):
    responses.get(SONGS_URL, status=404, json={"errors": [{"title": "Not Found"}]})

    assert apple.songs_by_isrc(["AB1"]) == {}


@responses.activate
def test_storefront_is_read_from_the_account(credentials):
    responses.get(f"{API_ROOT}/me/storefront", json={"data": [{"id": "gb"}]})

    assert AppleMusicClient.from_credentials(credentials).storefront == "gb"


@responses.activate
def test_storefront_falls_back_to_us(credentials):
    responses.get(f"{API_ROOT}/me/storefront", status=404)

    assert AppleMusicClient.from_credentials(credentials).storefront == "us"


@responses.activate
def test_storefront_raises_on_auth_errors(credentials):
    responses.get(f"{API_ROOT}/me/storefront", status=403, json={"errors": [{"detail": "Invalid token"}]})

    with pytest.raises(AppleMusicError, match="Music User Token"):
        AppleMusicClient.from_credentials(credentials).storefront


@responses.activate
def test_create_playlist(apple):
    responses.post(
        PLAYLISTS_URL,
        status=201,
        match=[matchers.json_params_matcher({"attributes": {"name": "Mix", "description": "d"}})],
        json={"data": [{"id": "p.123"}]},
    )

    assert apple.create_playlist("Mix", description="d") == "p.123"


@pytest.mark.parametrize("status, hint", [(401, "APPLE_KEY_ID"), (403, "Music User Token"), (400, "Bad")])
@responses.activate
def test_create_playlist_raises_with_a_useful_message(apple, status, hint):
    responses.post(PLAYLISTS_URL, status=status, json={"errors": [{"title": "Bad"}]})

    with pytest.raises(AppleMusicError, match=hint) as info:
        apple.create_playlist("Mix")
    assert info.value.status == status


@responses.activate
def test_add_tracks_sends_batches_in_order(apple):
    responses.post(TRACKS_URL, status=204)
    song_ids = [str(n) for n in range(60)]

    assert apple.add_tracks("p.123", song_ids) == [True] * 60
    assert [len(_sent_ids(call)) for call in responses.calls] == [25, 25, 10]
    assert sum((_sent_ids(call) for call in responses.calls), []) == song_ids


@responses.activate
def test_add_tracks_falls_back_to_single_songs_when_a_batch_is_rejected(apple):
    responses.post(
        TRACKS_URL,
        status=400,
        match=[
            matchers.json_params_matcher(
                {"data": [{"id": "1", "type": "songs"}, {"id": "bad", "type": "songs"}, {"id": "3", "type": "songs"}]}
            )
        ],
    )
    responses.post(
        TRACKS_URL, status=400, match=[matchers.json_params_matcher({"data": [{"id": "bad", "type": "songs"}]})]
    )
    responses.post(TRACKS_URL, status=204)

    assert apple.add_tracks("p.123", ["1", "bad", "3"]) == [True, False, True]


@responses.activate
def test_add_tracks_does_not_resend_after_a_server_error(apple):
    responses.post(TRACKS_URL, status=500)

    assert apple.add_tracks("p.123", ["1", "2"]) == [False, False]
    assert len(responses.calls) == 1


@responses.activate
def test_add_tracks_stops_on_auth_errors(apple):
    responses.post(TRACKS_URL, status=401)

    with pytest.raises(AppleMusicError):
        apple.add_tracks("p.123", ["1"])


@responses.activate
def test_rate_limited_requests_wait_and_retry(apple, sleeps):
    responses.post(TRACKS_URL, status=429, headers={"Retry-After": "7"})
    responses.post(TRACKS_URL, status=429)
    responses.post(TRACKS_URL, status=204)

    assert apple.add_tracks("p.123", ["1"]) == [True]
    assert sleeps == [7.0, 2.0]


@responses.activate
def test_reads_retry_server_errors_but_give_up_eventually(credentials, sleeps):
    client = AppleMusicClient.from_credentials(credentials, storefront="us", max_retries=2, sleep=sleeps.append)
    responses.get(SONGS_URL, status=503)

    with pytest.raises(AppleMusicError) as info:
        client.songs_by_isrc(["AB1"])
    assert info.value.status == 503
    assert len(responses.calls) == 3
    assert sleeps == [1.0, 2.0]
