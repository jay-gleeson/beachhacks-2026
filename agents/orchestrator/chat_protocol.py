import json
from datetime import datetime, timezone
from uuid import uuid4

from openai import OpenAI

from uagents import Context, Protocol
from agents.models.config import (
    OPENAI_API_KEY,
    SPOTIFY_ADDRESS,
    TASTE_ADDRESS,
    CONTEXT_ADDRESS,
    DISCOVERY_ADDRESS,
    PLAYLIST_ADDRESS,
)
from agents.models.models import SharedAgentState
from agents.services.state_service import state_service
from agents.services.spotify_service import has_user_token, get_auth_url
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

chat_proto = Protocol(spec=chat_protocol_spec)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

AGENT_MAP = {
    "spotify": SPOTIFY_ADDRESS,
    "taste": TASTE_ADDRESS,
    "context": CONTEXT_ADDRESS,
    "discovery": DISCOVERY_ADDRESS,
    "playlist": PLAYLIST_ADDRESS,
}

INITIAL_ROUTE_PROMPT = """You are an orchestrator that decides how to start fulfilling a user's playlist request.

Available agents:
- "spotify": Fetches the user's Spotify profile (top artists, top tracks). Needed for personalized playlists.
- "context": Parses the user's request to extract mood, activity, specific artists, genre, playlist name, track count.

User's request: "{query}"

Decide which agent to call FIRST:
- If the user wants a personalized playlist based on their taste (e.g. "make me a playlist", "something based on what I listen to"), start with "spotify".
- If the user mentions specific artists or a specific genre (e.g. "Frank Ocean songs", "edm playlist", "rock songs"), start with "context" — we don't need their Spotify profile.
- If unclear, default to "spotify" for the most personalized experience.

Respond with ONLY: spotify or context"""


def decide_initial_agent(query: str) -> str:
    """Use LLM to decide where to start the pipeline."""
    try:
        prompt = INITIAL_ROUTE_PROMPT.format(query=query)
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
        )
        decision = response.choices[0].message.content.strip().lower()
        if decision in AGENT_MAP:
            return decision
    except Exception as e:
        print(f"[chat_protocol] LLM initial routing failed: {e}")

    return "spotify"  # default


@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )

    text = " ".join(
        item.text for item in msg.content if isinstance(item, TextContent)
    )
    ctx.logger.info(f"Received: {text}")

    chat_session_id = str(ctx.session)

    # Check if user has connected their Spotify
    if not has_user_token(sender):
        auth_url = get_auth_url(sender)
        response = (
            f"Welcome! To create a personalized playlist, I need access to your Spotify account.\n\n"
            f"Click here to connect: {auth_url}\n\n"
            f"Once connected, send your request again!"
        )
        await ctx.send(
            sender,
            ChatMessage(
                timestamp=datetime.now(tz=timezone.utc),
                msg_id=uuid4(),
                content=[
                    TextContent(type="text", text=response),
                    EndSessionContent(type="end-session"),
                ],
            ),
        )
        return

    # Decide where to start
    first_agent = decide_initial_agent(text)
    ctx.logger.info(f"LLM decided to start with: {first_agent}")

    state = state_service.get_state(chat_session_id)

    if state is None:
        state = SharedAgentState(
            chat_session_id=chat_session_id,
            query=text,
            user_sender_address=sender,
            pipeline_stage=first_agent,
        )
        state_service.set_state(chat_session_id, state)
    else:
        state.query = text
        state.pipeline_stage = first_agent
        # Reset pipeline data for new request
        state.pipeline_data = "{}"
        state.result = ""

    # Record and route — import here to avoid circular
    from agents.orchestrator.orchestrator_fetchai_wrapped_agent import record_agent_call, _session_history
    # Clear history for new request
    _session_history[chat_session_id] = []
    record_agent_call(chat_session_id, first_agent)

    await ctx.send(AGENT_MAP[first_agent], state)
    ctx.logger.info(f"Pipeline started — routing to {first_agent}")


@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass
