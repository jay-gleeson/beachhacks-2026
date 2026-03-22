import json
import re

from openai import OpenAI

from agents.models.config import CONTEXT_SEED, OPENAI_API_KEY
from agents.models.models import SharedAgentState
from uagents import Agent, Context

context_agent = Agent(
    name="context",
    seed=CONTEXT_SEED,
    port=8006,
    mailbox=True,
    publish_agent_details=True,
)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

CONTEXT_PROMPT = """Analyze this playlist request from a user.

User's request: "{query}"

Respond with ONLY valid JSON, no markdown, no code blocks. Use this exact format:
{{
  "mood": "one of: chill, hype, sad, happy, focus, energetic, romantic, angry, mixed",
  "activity": "one of: studying, working out, driving, sleeping, cooking, hanging out, party, working, listening",
  "requested_artists": ["list of specific artist names mentioned, empty if none"],
  "requested_genre": "specific genre/style if mentioned (e.g. edm, jazz, country, rock, rap), empty string if none",
  "playlist_name": "custom playlist name if the user specified one, empty string if none",
  "track_count": number between 1-50 (default 10 if not specified)
}}

Examples:
- "give me a chill playlist" -> {{"mood": "chill", "activity": "listening", "requested_artists": [], "requested_genre": "", "playlist_name": "", "track_count": 10}}
- "I want Frank Ocean and Tyler the Creator songs" -> {{"mood": "chill", "activity": "listening", "requested_artists": ["Frank Ocean", "Tyler the Creator"], "requested_genre": "", "playlist_name": "", "track_count": 10}}
- "15 hype workout songs by Drake" -> {{"mood": "hype", "activity": "working out", "requested_artists": ["Drake"], "requested_genre": "", "playlist_name": "", "track_count": 15}}
- "get me a playlist of edm songs" -> {{"mood": "hype", "activity": "listening", "requested_artists": [], "requested_genre": "edm", "playlist_name": "", "track_count": 10}}
- "make a playlist called Summer Vibes with indie music" -> {{"mood": "chill", "activity": "listening", "requested_artists": [], "requested_genre": "indie", "playlist_name": "Summer Vibes", "track_count": 10}}
- "20 songs named indiana songs! that is indie" -> {{"mood": "chill", "activity": "listening", "requested_artists": [], "requested_genre": "indie", "playlist_name": "indiana songs!", "track_count": 20}}"""

MOOD_KEYWORDS = {
    "chill": ["chill", "relax", "calm", "mellow", "laid back", "easy", "peaceful", "soft"],
    "hype": ["hype", "pump", "turnt", "lit", "party", "rage", "wild", "crazy", "hard"],
    "sad": ["sad", "melancholy", "heartbreak", "cry", "emotional", "down", "lonely", "miss"],
    "happy": ["happy", "upbeat", "cheerful", "bright", "fun", "good vibes", "joyful", "excited"],
    "focus": ["focus", "study", "concentrate", "work", "productive", "grind", "deep work"],
    "energetic": ["workout", "gym", "run", "exercise", "training", "cardio", "lifting", "energy"],
    "romantic": ["romantic", "love", "date", "intimate", "sensual", "sexy"],
    "angry": ["angry", "aggressive", "mad", "heavy", "intense", "brutal"],
}

ACTIVITY_KEYWORDS = {
    "studying": ["study", "studying", "homework", "exam", "reading", "library"],
    "working out": ["workout", "gym", "run", "exercise", "training", "cardio", "lifting"],
    "driving": ["drive", "driving", "road trip", "car", "commute"],
    "sleeping": ["sleep", "sleeping", "bedtime", "wind down", "rest"],
    "cooking": ["cook", "cooking", "kitchen", "baking"],
    "hanging out": ["hang", "friends", "kickback", "hangout", "pregame"],
    "party": ["party", "club", "dance", "rave", "festival"],
    "working": ["work", "office", "productive", "grind", "coding"],
}


def parse_mood_fallback(query: str) -> str:
    query_lower = query.lower()
    for mood, keywords in MOOD_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                return mood
    return "chill"


def parse_activity_fallback(query: str) -> str:
    query_lower = query.lower()
    for activity, keywords in ACTIVITY_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                return activity
    return "listening"


def parse_track_count_fallback(query: str) -> int:
    match = re.search(r"(\d+)\s+\w*\s*(song|track|songs|tracks)", query.lower())
    if not match:
        match = re.search(r"(\d+)\s*(song|track|songs|tracks)", query.lower())
    if match:
        count = int(match.group(1))
        return min(max(count, 1), 50)
    return 10


def context_workflow(state: SharedAgentState) -> SharedAgentState:
    data = json.loads(state.pipeline_data)

    try:
        prompt = CONTEXT_PROMPT.format(query=state.query)
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        context = json.loads(response.choices[0].message.content.strip())
        context["raw_query"] = state.query
    except Exception as e:
        print(f"OpenAI context parsing failed, using fallback: {e}")
        context = {
            "mood": parse_mood_fallback(state.query),
            "activity": parse_activity_fallback(state.query),
            "requested_artists": [],
            "track_count": parse_track_count_fallback(state.query),
            "raw_query": state.query,
        }

    data["context"] = context
    state.pipeline_data = json.dumps(data)
    state.pipeline_stage = "discovery"
    return state


@context_agent.on_message(SharedAgentState)
async def handle_message(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(
        f"Received state from orchestrator: session={state.chat_session_id}, query={state.query!r}"
    )
    state = context_workflow(state)
    ctx.logger.info(f"Context parsed, forwarding to discovery stage")
    await ctx.send(sender, state)


if __name__ == "__main__":
    context_agent.run()
