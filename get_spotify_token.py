"""
Gets a Spotify user access token by running a local HTTP server to catch the callback.
"""

import base64
import subprocess
import urllib.parse
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests

from dotenv import load_dotenv
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8000/callback")
SCOPES = "user-top-read playlist-modify-public playlist-modify-private"

auth_code = None


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
            self.wfile.write(b"<h1>Success! You can close this tab.</h1>")
        else:
            self.wfile.write(b"<h1>Error: no code received</h1>")

    def log_message(self, format, *args):
        pass  # suppress logs


server = HTTPServer(("127.0.0.1", 8000), CallbackHandler)

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

print(f"\nOpening browser...\n")
subprocess.run(["open", auth_url])

print("Waiting for callback (approve in browser)...\n")
while auth_code is None:
    server.handle_request()

server.server_close()

# Exchange code for token
auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
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
    print(f"SUCCESS! Your access token:\n")
    print(response["access_token"])
    print(f"\nExpires in: {response.get('expires_in', '?')} seconds")
    print(f"\nPaste this into your .env as SPOTIFY_TOKEN")
else:
    print(f"ERROR: {response}")
