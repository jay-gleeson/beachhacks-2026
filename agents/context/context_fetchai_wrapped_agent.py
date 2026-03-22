import json
import re

from agents.models.config import CONTEXT_SEED
from agents.models.models import SharedAgentState
from uagents import Agent, Context

context_agent = Agent(
    name="context",
    seed=CONTEXT_SEED,
    port=8006,
    mailbox=True,
    publish_agent_details=True,
)

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


def parse_mood(query: str) -> str:
    query_lower = query.lower()
    for mood, keywords in MOOD_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                return mood
    return "chill"


def parse_activity(query: str) -> str:
    query_lower = query.lower()
    for activity, keywords in ACTIVITY_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                return activity
    return "listening"


def parse_track_count(query: str) -> int:
    match = re.search(r"(\d+)\s*(song|track|songs|tracks)", query.lower())
    if match:
        count = int(match.group(1))
        return min(max(count, 1), 20)
    return 10


def context_workflow(state: SharedAgentState) -> SharedAgentState:
    data = json.loads(state.pipeline_data)

    context = {
        "mood": parse_mood(state.query),
        "activity": parse_activity(state.query),
        "track_count": parse_track_count(state.query),
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
