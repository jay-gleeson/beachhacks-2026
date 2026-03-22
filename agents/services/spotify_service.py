"""
Spotify helper functions using spotipy SDK.
Supports per-user tokens with auto-refresh.
Falls back to the global .env token if no per-user token exists.
"""

import base64
import os
import re
from pathlib import Path

import requests as http_requests
import spotipy
from dotenv import load_dotenv

from agents.services.token_store import get_user_tokens, update_access_token

ENV_PATH = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ENV_PATH, override=True)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Fallback global token from .env (for your own account / demo)
_global_token = os.getenv("SPOTIFY_TOKEN")
_global_refresh = os.getenv("SPOTIFY_REFRESH_TOKEN")

AUTH_SERVER_URL = "http://127.0.0.1:9999"


def _refresh_token(refresh_token: str) -> str | None:
    """Use a refresh token to get a new access token."""
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
        return response["access_token"]
    print(f"[spotify_service] Token refresh failed: {response}")
    return None


def get_auth_url(user_address: str) -> str:
    """Get the URL to send a user to connect their Spotify."""
    return f"{AUTH_SERVER_URL}/login?user={user_address}"


def get_spotify_client(user_address: str = "") -> spotipy.Spotify | None:
    """Get a Spotify client for a specific user, or fall back to global token."""
    global _global_token

    token = None
    refresh = None

    # Try per-user token first
    if user_address:
        user_tokens = get_user_tokens(user_address)
        if user_tokens:
            token = user_tokens["access_token"]
            refresh = user_tokens["refresh_token"]

    # Fall back to global token
    if not token:
        token = _global_token
        refresh = _global_refresh

    if not token:
        return None

    sp = spotipy.Spotify(auth=token)

    # Test if token is still valid
    try:
        sp.current_user()
        return sp
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 401 and refresh:
            print("[spotify_service] Token expired, refreshing...")
            new_token = _refresh_token(refresh)
            if new_token:
                # Save refreshed token
                if user_address and get_user_tokens(user_address):
                    update_access_token(user_address, new_token)
                else:
                    _global_token = new_token
                return spotipy.Spotify(auth=new_token)
        return None


def has_user_token(user_address: str) -> bool:
    """Check if a user has connected their Spotify."""
    return get_user_tokens(user_address) is not None


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
    token = sp._auth if hasattr(sp, '_auth') else _global_token
    res = http_requests.post(
        "https://api.spotify.com/v1/me/playlists",
        headers={
            "Authorization": f"Bearer {token}",
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
