"""
Spotify helper functions using spotipy SDK.
Centralizes all Spotify API interactions.
Auto-refreshes token when expired.
"""

import base64
import os
import re
from pathlib import Path

import requests as http_requests
import spotipy
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent.parent.parent / ".env"

# Load fresh env vars
load_dotenv(ENV_PATH, override=True)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

_current_token = os.getenv("SPOTIFY_TOKEN")


def _save_to_env(key: str, value: str) -> None:
    """Update or add a key=value in the .env file."""
    env_text = ENV_PATH.read_text()
    pattern = rf"^{re.escape(key)}=.*$"
    if re.search(pattern, env_text, flags=re.MULTILINE):
        env_text = re.sub(pattern, f"{key}={value}", env_text, flags=re.MULTILINE)
    else:
        env_text = env_text.rstrip() + f"\n{key}={value}\n"
    ENV_PATH.write_text(env_text)


def _refresh_token() -> str | None:
    """Use the refresh token to get a new access token."""
    global _current_token

    refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
    if not refresh_token:
        print("[spotify_service] No refresh token available")
        return None

    auth_header = base64.b64encode(
        f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()

    response = http_requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {auth_header}"},
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    ).json()

    if "access_token" in response:
        _current_token = response["access_token"]
        _save_to_env("SPOTIFY_TOKEN", _current_token)
        if "refresh_token" in response:
            _save_to_env("SPOTIFY_REFRESH_TOKEN", response["refresh_token"])
        print("[spotify_service] Token refreshed successfully")
        return _current_token

    print(f"[spotify_service] Token refresh failed: {response}")
    return None


def get_spotify_client() -> spotipy.Spotify | None:
    global _current_token

    if not _current_token:
        return None

    sp = spotipy.Spotify(auth=_current_token)

    # Test if token is still valid
    try:
        sp.current_user()
        return sp
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 401:
            print("[spotify_service] Token expired, attempting refresh...")
            new_token = _refresh_token()
            if new_token:
                return spotipy.Spotify(auth=new_token)
        return None


def get_user_top_artists(sp: spotipy.Spotify, limit: int = 5) -> list[dict]:
    results = sp.current_user_top_artists(limit=limit)
    return [
        {"name": a["name"], "id": a["id"]}
        for a in results["items"]
    ]


def get_user_top_tracks(sp: spotipy.Spotify, limit: int = 5) -> list[str]:
    results = sp.current_user_top_tracks(limit=limit)
    return [t["name"] for t in results["items"]]


def search_tracks(sp: spotipy.Spotify, query: str, limit: int = 10) -> list[dict]:
    """Search for tracks on Spotify."""
    results = sp.search(q=query, type="track", limit=limit)
    return [
        {
            "title": t["name"],
            "artist": t["artists"][0]["name"],
            "album": t["album"]["name"],
            "uri": t["uri"],
        }
        for t in results["tracks"]["items"]
    ]


def create_playlist(sp: spotipy.Spotify, name: str, description: str = "") -> str:
    """Create a playlist using POST /me/playlists. Returns the playlist ID."""
    global _current_token
    res = http_requests.post(
        "https://api.spotify.com/v1/me/playlists",
        headers={
            "Authorization": f"Bearer {_current_token}",
            "Content-Type": "application/json",
        },
        json={
            "name": name,
            "public": True,
            "description": description,
        },
    )
    res.raise_for_status()
    return res.json()["id"]


def add_tracks_to_playlist(sp: spotipy.Spotify, playlist_id: str, track_uris: list[str]) -> None:
    """Add tracks to a playlist using POST /playlists/{id}/items."""
    sp.playlist_add_items(playlist_id, track_uris)
