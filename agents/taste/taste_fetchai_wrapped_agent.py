import json

from openai import OpenAI

from agents.models.config import TASTE_SEED, OPENAI_API_KEY
from agents.models.models import SharedAgentState
from uagents import Agent, Context

taste_agent = Agent(
    name="taste",
    seed=TASTE_SEED,
    port=8005,
    mailbox=True,
    publish_agent_details=True,
)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

TASTE_PROMPT = """Given these top artists and tracks from a user's Spotify profile, analyze their music taste.

Top Artists: {artists}
Top Tracks: {tracks}

Respond with ONLY valid JSON, no markdown, no code blocks. Use this exact format:
{{
  "primary_genre": "the main genre",
  "secondary_genre": "the second most prominent genre",
  "all_genres": ["list", "of", "all", "detected", "genres"],
  "energy": "low" or "medium" or "high",
  "mood": "a 2-3 word mood description",
  "summary": "A single sentence describing this person's music taste"
}}"""


def taste_workflow(state: SharedAgentState) -> SharedAgentState:
    data = json.loads(state.pipeline_data)
    profile = data.get("spotify_profile", {})
    top_artists = profile.get("top_artists", [])
    top_tracks = profile.get("top_tracks", [])

    try:
        prompt = TASTE_PROMPT.format(
            artists=", ".join(top_artists),
            tracks=", ".join(top_tracks),
        )
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        taste_profile = json.loads(response.choices[0].message.content.strip())
        taste_profile["top_artists"] = top_artists
    except Exception as e:
        print(f"OpenAI API failed, using fallback taste profile: {e}")
        taste_profile = {
            "primary_genre": "mixed",
            "secondary_genre": "mixed",
            "all_genres": ["mixed"],
            "energy": "medium",
            "mood": "eclectic vibes",
            "summary": "A diverse listener with varied taste.",
            "top_artists": top_artists,
        }

    data["taste_profile"] = taste_profile
    state.pipeline_data = json.dumps(data)
    state.pipeline_stage = "context"
    return state


@taste_agent.on_message(SharedAgentState)
async def handle_message(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(
        f"Received state from orchestrator: session={state.chat_session_id}, query={state.query!r}"
    )
    state = taste_workflow(state)
    ctx.logger.info(f"Taste profile built, forwarding to context stage")
    await ctx.send(sender, state)


if __name__ == "__main__":
    taste_agent.run()
