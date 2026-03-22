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


def discover_tracks(top_artists: list[str], taste: dict, context: dict, track_count: int, user_address: str = "") -> list[dict]:
    """Search Spotify for tracks based on the user's taste and requested mood."""
    sp = get_spotify_client(user_address=user_address)
    if not sp:
        return []

    mood = context.get("mood", "chill")
    genres = taste.get("all_genres", [])
    requested_artists = context.get("requested_artists", [])
    candidate_tracks = []
    seen_uris = set()

    requested_genre = context.get("requested_genre", "")

    if requested_artists:
        # User asked for specific artists — prioritize those
        for artist in requested_artists:
            try:
                query = f'artist:"{artist}"'
                tracks = search_tracks(sp, query, limit=10)
                for t in tracks:
                    if t["uri"] not in seen_uris and artist.lower() in t["artist"].lower():
                        seen_uris.add(t["uri"])
                        candidate_tracks.append(t)
            except Exception as e:
                print(f"[DEBUG] Search failed for requested artist {artist}: {e}")
    elif requested_genre:
        # User asked for a specific genre — search by genre
        try:
            query = f"genre:{requested_genre}"
            tracks = search_tracks(sp, query, limit=track_count + 10)
            for t in tracks:
                if t["uri"] not in seen_uris:
                    seen_uris.add(t["uri"])
                    candidate_tracks.append(t)
        except Exception as e:
            print(f"[DEBUG] Search failed for genre {requested_genre}: {e}")

        # Also try mood + genre combo for variety
        try:
            query = f"{requested_genre} {mood}"
            tracks = search_tracks(sp, query, limit=track_count)
            for t in tracks:
                if t["uri"] not in seen_uris:
                    seen_uris.add(t["uri"])
                    candidate_tracks.append(t)
        except Exception as e:
            print(f"[DEBUG] Search failed for {requested_genre} {mood}: {e}")
    else:
        # No specific request — use their top artists heavily
        # Search more artists with more tracks each for variety
        artists_to_search = min(len(top_artists), 15)
        tracks_per_artist = max(3, track_count // artists_to_search + 1)

        for artist in top_artists[:artists_to_search]:
            try:
                query = f'artist:"{artist}"'
                tracks = search_tracks(sp, query, limit=min(tracks_per_artist, 10))
                # Filter: only keep tracks where the artist name actually matches
                for t in tracks:
                    if t["uri"] not in seen_uris and artist.lower() in t["artist"].lower():
                        seen_uris.add(t["uri"])
                        candidate_tracks.append(t)
            except Exception as e:
                print(f"[DEBUG] Search failed for artist {artist}: {e}")

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
            recommendations = discover_tracks(top_artists, taste, context, track_count, state.user_sender_address)
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
