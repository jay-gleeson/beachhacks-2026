"""
Spotify OAuth server for per-user authentication.
Users click a link from ASI:One chat, authenticate with Spotify,
and their token gets saved mapped to their ASI:One address.

Run this alongside your agents:
    .venv/bin/python spotify_auth_server.py
"""

import base64
import os
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests
from dotenv import load_dotenv

# Add agents to path so we can import token_store
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))

from agents.services.token_store import set_user_tokens

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:9999/callback"
SCOPES = "user-top-read playlist-modify-public playlist-modify-private"
AUTH_SERVER_PORT = 9999

# Temporary storage for pending auth requests
pending_auth = {}


class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/login":
            # User clicked the auth link from ASI:One
            user_address = params.get("user", [None])[0]
            if not user_address:
                self._respond(400, "Missing user parameter")
                return

            # Store the user address and redirect to Spotify
            import uuid
            state = str(uuid.uuid4())
            pending_auth[state] = user_address

            auth_url = (
                "https://accounts.spotify.com/authorize?"
                + urllib.parse.urlencode(
                    {
                        "client_id": CLIENT_ID,
                        "response_type": "code",
                        "redirect_uri": REDIRECT_URI,
                        "scope": SCOPES,
                        "state": state,
                        "show_dialog": "true",
                    }
                )
            )
            self.send_response(302)
            self.send_header("Location", auth_url)
            self.end_headers()

        elif parsed.path == "/callback":
            # Spotify redirected back with the auth code
            code = params.get("code", [None])[0]
            state = params.get("state", [None])[0]

            if not code or not state or state not in pending_auth:
                self._respond(400, "Invalid callback")
                return

            user_address = pending_auth.pop(state)

            # Exchange code for tokens
            auth_header = base64.b64encode(
                f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
            ).decode()

            response = requests.post(
                "https://accounts.spotify.com/api/token",
                headers={"Authorization": f"Basic {auth_header}"},
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                },
            ).json()

            if "access_token" in response:
                set_user_tokens(
                    user_address,
                    response["access_token"],
                    response.get("refresh_token", ""),
                )
                self._respond(
                    200,
                    "<h1>Connected to Spotify!</h1>"
                    "<p>You can close this tab and go back to ASI:One.</p>"
                    "<p>Send your playlist request again and it will use your real Spotify data.</p>"
                )
            else:
                self._respond(500, f"<h1>Error</h1><p>{response}</p>")
        else:
            self._respond(404, "Not found")

    def _respond(self, status: int, body: str):
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, format, *args):
        print(f"[auth-server] {args[0]}")


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", AUTH_SERVER_PORT), AuthHandler)
    print(f"\nSpotify auth server running on http://127.0.0.1:{AUTH_SERVER_PORT}")
    print("Users will be directed here from ASI:One to connect their Spotify.\n")
    server.serve_forever()
