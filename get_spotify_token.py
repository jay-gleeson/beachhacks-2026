"""
Spotify OAuth helper — run this once to authenticate.
Opens browser, user logs in, token auto-saves to .env.
Also stores a refresh token so you can re-run without the browser flow.
"""

import base64
import os
import re
import subprocess
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import requests
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8000/callback")
SCOPES = "user-top-read playlist-modify-public playlist-modify-private"

auth_code = None


def save_token_to_env(key: str, value: str) -> None:
    """Update or add a key=value in the .env file."""
    env_text = ENV_PATH.read_text()

    pattern = rf"^{re.escape(key)}=.*$"
    if re.search(pattern, env_text, flags=re.MULTILINE):
        env_text = re.sub(pattern, f"{key}={value}", env_text, flags=re.MULTILINE)
    else:
        env_text = env_text.rstrip() + f"\n{key}={value}\n"

    ENV_PATH.write_text(env_text)


def refresh_existing_token() -> bool:
    """Try to refresh using an existing refresh token. Returns True if successful."""
    refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
    if not refresh_token:
        return False

    print("Found refresh token — refreshing without browser...")
    auth_header = base64.b64encode(
        f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {auth_header}"},
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    ).json()

    if "access_token" in response:
        save_token_to_env("SPOTIFY_TOKEN", response["access_token"])
        # Spotify may return a new refresh token
        if "refresh_token" in response:
            save_token_to_env("SPOTIFY_REFRESH_TOKEN", response["refresh_token"])
        print(f"Token refreshed! Expires in {response.get('expires_in', '?')} seconds.")
        return True

    print(f"Refresh failed: {response.get('error_description', response)}")
    return False


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        auth_code = params.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        if auth_code:
            self.wfile.write(
                b"<h1>Success! You can close this tab and go back to your terminal.</h1>"
            )
        else:
            self.wfile.write(b"<h1>Error: no code received</h1>")

    def log_message(self, format, *args):
        pass


def do_full_auth():
    """Full OAuth flow — opens browser, catches callback."""
    global auth_code

    port = int(urllib.parse.urlparse(SPOTIFY_REDIRECT_URI).port or 8000)
    server = HTTPServer(("127.0.0.1", port), CallbackHandler)

    auth_url = (
        "https://accounts.spotify.com/authorize?"
        + urllib.parse.urlencode(
            {
                "client_id": SPOTIFY_CLIENT_ID,
                "response_type": "code",
                "redirect_uri": SPOTIFY_REDIRECT_URI,
                "scope": SCOPES,
                "show_dialog": "true",
            }
        )
    )

    print("\nOpening browser — log in to Spotify and approve...\n")
    subprocess.run(["open", auth_url])

    while auth_code is None:
        server.handle_request()

    server.server_close()

    # Exchange code for tokens
    auth_header = base64.b64encode(
        f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {auth_header}"},
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": SPOTIFY_REDIRECT_URI,
        },
    ).json()

    if "access_token" in response:
        save_token_to_env("SPOTIFY_TOKEN", response["access_token"])
        if "refresh_token" in response:
            save_token_to_env("SPOTIFY_REFRESH_TOKEN", response["refresh_token"])

        print(f"Authenticated! Token saved to .env")
        print(f"Expires in {response.get('expires_in', '?')} seconds.")
        print(f"Next time, just re-run this script — it'll auto-refresh without the browser.")
    else:
        print(f"ERROR: {response}")


if __name__ == "__main__":
    # Try refresh first, fall back to full auth
    if not refresh_existing_token():
        do_full_auth()
