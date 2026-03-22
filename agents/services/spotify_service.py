"""
Spotify helper functions using spotipy SDK.
Centralizes all Spotify API interactions.
"""

import spotipy
from agents.models.config import SPOTIFY_TOKEN


def get_spotify_client() -> spotipy.Spotify | None:
    if not SPOTIFY_TOKEN:
        return None
    return spotipy.Spotify(auth=SPOTIFY_TOKEN)


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
    import requests
    res = requests.post(
        "https://api.spotify.com/v1/me/playlists",
        headers={
            "Authorization": f"Bearer {SPOTIFY_TOKEN}",
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
