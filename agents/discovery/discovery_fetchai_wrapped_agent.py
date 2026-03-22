import json
import random

import requests

from agents.models.config import DISCOVERY_SEED, SPOTIFY_TOKEN
from agents.models.models import SharedAgentState
from agents.discovery.song_pool import MOCK_SONGS
from uagents import Agent, Context

discovery_agent = Agent(
    name="discovery",
    seed=DISCOVERY_SEED,
    port=8007,
    mailbox=True,
    publish_agent_details=True,
)


def get_related_tracks(artist_ids: list[str], token: str, track_count: int) -> list[dict]:
    """Find tracks by getting related artists and their top tracks."""
    headers = {"Authorization": f"Bearer {token}"}
    candidate_tracks = []

    # Get related artists for top 2-3 seed artists
    related_artist_ids = []
    for artist_id in artist_ids[:3]:
        try:
            res = requests.get(
                f"https://api.spotify.com/v1/artists/{artist_id}/related-artists",
                headers=headers,
            ).json()
            for artist in res.get("artists", [])[:5]:
                related_artist_ids.append(artist["id"])
        except Exception as e:
            print(f"[DEBUG] Failed to get related artists for {artist_id}: {e}")

    if not related_artist_ids:
        return []

    # Shuffle and pick a subset for variety
    random.shuffle(related_artist_ids)
    selected_artists = related_artist_ids[:6]

    # Get top tracks for each selected related artist
    for artist_id in selected_artists:
        try:
            res = requests.get(
                f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
                headers=headers,
            ).json()
            for track in res.get("tracks", [])[:3]:
                candidate_tracks.append({
                    "title": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": track["album"]["name"],
                })
        except Exception as e:
            print(f"[DEBUG] Failed to get top tracks for {artist_id}: {e}")

    # Shuffle and trim to requested count
    random.shuffle(candidate_tracks)
    return candidate_tracks[:track_count]


def discovery_workflow(state: SharedAgentState) -> SharedAgentState:
    data = json.loads(state.pipeline_data)
    profile = data.get("spotify_profile", {})
    context = data.get("context", {})
    artist_ids = profile.get("top_artist_ids", [])
    track_count = context.get("track_count", 10)

    recommendations = []

    try:
        if SPOTIFY_TOKEN and artist_ids:
            recommendations = get_related_tracks(artist_ids, SPOTIFY_TOKEN, track_count)
    except Exception as e:
        print(f"Discovery API failed, falling back to mock: {e}")

    # Fallback to mock songs if we got nothing
    if not recommendations:
        pool = list(MOCK_SONGS)
        random.shuffle(pool)
        recommendations = pool[:track_count]

    data["recommendations"] = recommendations
    state.pipeline_data = json.dumps(data)
    state.pipeline_stage = "playlist"
    return state


@discovery_agent.on_message(SharedAgentState)
async def handle_message(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(
        f"Received state from orchestrator: session={state.chat_session_id}, query={state.query!r}"
    )
    state = discovery_workflow(state)
    ctx.logger.info(f"Discovery complete, forwarding to playlist stage")
    await ctx.send(sender, state)


if __name__ == "__main__":
    discovery_agent.run()
