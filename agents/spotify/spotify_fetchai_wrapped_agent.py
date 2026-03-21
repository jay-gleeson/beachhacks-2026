import json

import requests

from agents.models.config import SPOTIFY_SEED, SPOTIFY_TOKEN
from agents.models.models import SharedAgentState
from uagents import Agent, Context

spotify_agent = Agent(
    name="spotify",
    seed=SPOTIFY_SEED,
    port=8004,
    mailbox=True,
    publish_agent_details=True,
)


MOCK_PROFILE = {
    "top_artists": ["Tame Impala", "Kendrick Lamar", "SZA", "Frank Ocean", "Bonobo"],
    "top_artist_ids": [
        "5INjqkS1o8h1imAzPqGZBb",
        "2YZyLoL8N0Wb9xBt1NhZWg",
        "7tYKF4w9nC0nq9CsPZTHyP",
        "2h93pZq0e7k5yf4dywlkpM",
        "0cmWgDlu9CwTgxPhf403hb",
    ],
    "top_tracks": [
        "The Less I Know The Better",
        "HUMBLE.",
        "Snooze",
        "Nights",
        "Kerala",
    ],
}


def get_real_profile(token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}

    artists_res = requests.get(
        "https://api.spotify.com/v1/me/top/artists",
        headers=headers,
        params={"limit": 5},
    ).json()

    tracks_res = requests.get(
        "https://api.spotify.com/v1/me/top/tracks",
        headers=headers,
        params={"limit": 5},
    ).json()

    top_artists = [a["name"] for a in artists_res["items"]]
    top_artist_ids = [a["id"] for a in artists_res["items"]]
    top_tracks = [t["name"] for t in tracks_res["items"]]

    return {
        "top_artists": top_artists,
        "top_artist_ids": top_artist_ids,
        "top_tracks": top_tracks,
    }


def spotify_workflow(state: SharedAgentState) -> SharedAgentState:
    try:
        if SPOTIFY_TOKEN:
            profile = get_real_profile(SPOTIFY_TOKEN)
        else:
            profile = MOCK_PROFILE
    except Exception as e:
        print(f"Spotify API failed, falling back to mock: {e}")
        profile = MOCK_PROFILE

    data = json.loads(state.pipeline_data)
    data["spotify_profile"] = profile
    state.pipeline_data = json.dumps(data)
    state.pipeline_stage = "taste"
    return state


@spotify_agent.on_message(SharedAgentState)
async def handle_message(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(
        f"Received state from orchestrator: session={state.chat_session_id}, query={state.query!r}"
    )
    state = spotify_workflow(state)
    ctx.logger.info(f"Spotify profile fetched, forwarding to taste stage")
    await ctx.send(sender, state)


if __name__ == "__main__":
    spotify_agent.run()
