from datetime import datetime, timezone
from uuid import uuid4

from uagents import Context, Protocol
from agents.models.config import SPOTIFY_ADDRESS
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

    state = state_service.get_state(chat_session_id)

    if state is None:
        state = SharedAgentState(
            chat_session_id=chat_session_id,
            query=text,
            user_sender_address=sender,
            pipeline_stage="spotify",
        )
        state_service.set_state(chat_session_id, state)
    else:
        state.query = text
        state.pipeline_stage = "spotify"

    # Start the pipeline — send to SpotifyAgent
    await ctx.send(SPOTIFY_ADDRESS, state)
    ctx.logger.info("Pipeline started — routing to SpotifyAgent")


@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


def generate_orchestrator_response_from_state(state: SharedAgentState) -> str:
    return state.result
