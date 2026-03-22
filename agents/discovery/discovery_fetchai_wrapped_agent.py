import json
import random

from agents.models.config import DISCOVERY_SEED
from agents.models.models import SharedAgentState
from agents.services.spotify_service import get_spotify_client, search_tracks
from agents.discovery.song_pool import MOCK_SONGS
from uagents import Agent, Context

discovery_agent = Agent(
    name="discovery",
    seed=DISCOVERY_SEED,
    port=8007,
    mailbox=True,
    publish_agent_details=True,
)


def discover_tracks(top_artists: list[str], taste: dict, context: dict, track_count: int) -> list[dict]:
    """Search Spotify for tracks based on the user's taste and requested mood."""
    sp = get_spotify_client()
    if not sp:
        return []

    mood = context.get("mood", "chill")
    genres = taste.get("all_genres", [])
    candidate_tracks = []
    seen_uris = set()

    # Search by top artists (most personalized)
    for artist in top_artists[:3]:
        try:
            query = f"artist:{artist}"
            tracks = search_tracks(sp, query, limit=5)
            for t in tracks:
                if t["uri"] not in seen_uris:
                    seen_uris.add(t["uri"])
                    candidate_tracks.append(t)
        except Exception as e:
            print(f"[DEBUG] Search failed for artist {artist}: {e}")

    # Search by genres + mood for discovery
    for genre in genres[:2]:
        try:
            query = f"genre:{genre} {mood}"
            tracks = search_tracks(sp, query, limit=5)
            for t in tracks:
                if t["uri"] not in seen_uris:
                    seen_uris.add(t["uri"])
                    candidate_tracks.append(t)
        except Exception as e:
            print(f"[DEBUG] Search failed for genre {genre}: {e}")

    # Shuffle for variety and trim
    random.shuffle(candidate_tracks)
    return candidate_tracks[:track_count]


def discovery_workflow(state: SharedAgentState) -> SharedAgentState:
    data = json.loads(state.pipeline_data)
    profile = data.get("spotify_profile", {})
    taste = data.get("taste_profile", {})
    context = data.get("context", {})
    top_artists = profile.get("top_artists", [])
    track_count = context.get("track_count", 10)

    recommendations = []

    try:
        if top_artists:
            recommendations = discover_tracks(top_artists, taste, context, track_count)
    except Exception as e:
        print(f"Discovery failed, falling back to mock: {e}")

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
