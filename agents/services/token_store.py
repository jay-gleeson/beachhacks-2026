"""
Per-user Spotify token storage.
Maps ASI:One user addresses to their Spotify access + refresh tokens.
Persists to a JSON file so tokens survive restarts.
"""

import json
from pathlib import Path

STORE_PATH = Path(__file__).parent.parent.parent / "spotify_tokens.json"


def _load() -> dict:
    if STORE_PATH.exists():
        return json.loads(STORE_PATH.read_text())
    return {}


def _save(store: dict) -> None:
    STORE_PATH.write_text(json.dumps(store, indent=2))


def get_user_tokens(user_address: str) -> dict | None:
    """Get tokens for a user. Returns {access_token, refresh_token} or None."""
    store = _load()
    return store.get(user_address)


def set_user_tokens(user_address: str, access_token: str, refresh_token: str) -> None:
    """Save tokens for a user."""
    store = _load()
    store[user_address] = {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
    _save(store)


def update_access_token(user_address: str, access_token: str) -> None:
    """Update just the access token for a user."""
    store = _load()
    if user_address in store:
        store[user_address]["access_token"] = access_token
        _save(store)
