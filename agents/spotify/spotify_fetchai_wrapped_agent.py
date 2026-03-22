import json

from agents.models.config import SPOTIFY_SEED
from agents.models.models import SharedAgentState
from agents.services.spotify_service import get_spotify_client, get_user_top_artists, get_user_top_tracks
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


def spotify_workflow(state: SharedAgentState) -> SharedAgentState:
    try:
        sp = get_spotify_client()
        if sp:
            artists = get_user_top_artists(sp)
            top_tracks = get_user_top_tracks(sp)
            profile = {
                "top_artists": [a["name"] for a in artists],
                "top_artist_ids": [a["id"] for a in artists],
                "top_tracks": top_tracks,
            }
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
