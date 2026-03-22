import json
from datetime import datetime, timezone
from uuid import uuid4

from openai import OpenAI

from agents.models.config import (
    ORCHESTRATOR_SEED,
    OPENAI_API_KEY,
    SPOTIFY_ADDRESS,
    TASTE_ADDRESS,
    CONTEXT_ADDRESS,
    DISCOVERY_ADDRESS,
    PLAYLIST_ADDRESS,
)
from agents.models.models import SharedAgentState
from agents.orchestrator.chat_protocol import chat_proto
from uagents import Agent, Context, Model
from uagents_core.contrib.protocols.chat import ChatMessage, EndSessionContent, TextContent

orchestrator = Agent(
    name="orchestrator",
    seed=ORCHESTRATOR_SEED,
    port=8003,
    mailbox=True,
    publish_agent_details=True,
)

orchestrator.include(chat_proto, publish_manifest=True)

# Fix duplicate log output
import logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

AGENT_MAP = {
    "spotify": SPOTIFY_ADDRESS,
    "taste": TASTE_ADDRESS,
    "context": CONTEXT_ADDRESS,
    "discovery": DISCOVERY_ADDRESS,
    "playlist": PLAYLIST_ADDRESS,
}

ROUTER_PROMPT = """You are an orchestrator that decides which agent to call next to fulfill a user's playlist request.

Available agents:
- "spotify": Fetches the user's Spotify profile (top artists, top tracks).
- "taste": Analyzes the user's Spotify profile to determine genres, energy level, and vibe.
- "context": Parses the user's request to extract mood, activity, specific artists, genre, playlist name, track count.
- "discovery": Searches Spotify for tracks based on taste + context. Requires context data.
- "playlist": Formats and creates the playlist on Spotify. Requires recommendations.
- "done": Pipeline complete, send result to user.

User's original request: "{query}"

Agents already completed: {completed_agents}

Data gathered so far (keys only): {data_keys}

Has result ready to send: {has_result}

CRITICAL RULES:
- NEVER call an agent that is already in the completed list.
- If "context" is completed, the next step is "discovery".
- If "discovery" is completed, the next step is "playlist".
- If "playlist" is completed, respond with "done".
- If result is ready, respond with "done".
- For personalized playlists: spotify → taste → context → discovery → playlist
- For genre/artist-specific playlists: context → discovery → playlist (skip spotify and taste)

Respond with ONLY the agent name. No explanation."""


class HealthResponse(Model):
    status: str


@orchestrator.on_rest_get("/health", HealthResponse)
async def health(ctx: Context) -> HealthResponse:
    return HealthResponse(status="ok healthy")


# Track which agents have run per session to prevent loops
_session_history: dict[str, list[str]] = {}

MAX_AGENT_CALLS = 8  # Safety limit


def decide_next_agent(state: SharedAgentState) -> str:
    """Use LLM to decide which agent to call next, with loop prevention."""
    data = json.loads(state.pipeline_data)
    session = state.chat_session_id

    # Track completed agents
    if session not in _session_history:
        _session_history[session] = []
    completed = _session_history[session]

    # Safety: if we've called too many agents, force completion
    if len(completed) >= MAX_AGENT_CALLS:
        print(f"[orchestrator] Hit max agent calls ({MAX_AGENT_CALLS}), forcing done")
        return "done" if state.result else "playlist"

    # If result is set, we're done
    if state.result:
        return "done"

    # Determine what data we have
    data_keys = list(data.keys())

    try:
        prompt = ROUTER_PROMPT.format(
            query=state.query,
            completed_agents=", ".join(completed) if completed else "none",
            data_keys=", ".join(data_keys) if data_keys else "none",
            has_result="yes" if state.result else "no",
        )
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
        )
        decision = response.choices[0].message.content.strip().lower()

        # Validate: don't call an already-completed agent
        if decision in completed and decision != "done":
            print(f"[orchestrator] LLM tried to re-call {decision}, using fallback")
            # Fallback: use deterministic next step
            return _deterministic_next(completed, data_keys)

        if decision in AGENT_MAP or decision == "done":
            return decision

        print(f"[orchestrator] LLM returned invalid: {decision}, using fallback")
    except Exception as e:
        print(f"[orchestrator] LLM routing failed: {e}, using fallback")

    return _deterministic_next(completed, data_keys)


def _deterministic_next(completed: list[str], data_keys: list[str]) -> str:
    """Fallback deterministic routing when LLM fails or loops."""
    pipeline = ["spotify", "taste", "context", "discovery", "playlist"]
    for agent in pipeline:
        if agent not in completed:
            return agent
    return "done"


def record_agent_call(session: str, agent: str):
    """Record that an agent was called for this session."""
    if session not in _session_history:
        _session_history[session] = []
    _session_history[session].append(agent)


@orchestrator.on_message(SharedAgentState)
async def handle_agent_response(ctx: Context, sender: str, state: SharedAgentState):
    # Record which agent just completed (based on pipeline_stage it set)
    # The agent sets pipeline_stage to the NEXT stage, so the one that just ran is the previous one
    completed = _session_history.get(state.chat_session_id, [])

    # Decide what to do next
    next_step = decide_next_agent(state)
    ctx.logger.info(
        f"Received state: session={state.chat_session_id}, "
        f"agent_suggested={state.pipeline_stage}, llm_decided={next_step}, "
        f"history={completed}"
    )

    if next_step == "done":
        # Pipeline complete — send result back to user
        ctx.logger.info("Pipeline complete — sending result to user")
        await ctx.send(
            state.user_sender_address,
            ChatMessage(
                timestamp=datetime.now(tz=timezone.utc),
                msg_id=uuid4(),
                content=[
                    TextContent(type="text", text=state.result),
                    EndSessionContent(type="end-session"),
                ],
            ),
        )
    elif next_step in AGENT_MAP:
        record_agent_call(state.chat_session_id, next_step)
        ctx.logger.info(f"Routing to: {next_step}")
        state.pipeline_stage = next_step
        await ctx.send(AGENT_MAP[next_step], state)
    else:
        ctx.logger.error(f"Unknown decision: {next_step}")


if __name__ == "__main__":
    orchestrator.run()
