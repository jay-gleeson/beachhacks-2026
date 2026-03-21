from datetime import datetime, timezone
from uuid import uuid4

from agents.models.config import ORCHESTRATOR_SEED
from agents.models.models import SharedAgentState, BlendRequest, BlendResponse
from agents.orchestrator.chat_protocol import chat_proto, generate_orchestrator_response_from_state
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


class HealthResponse(Model):
    status: str


@orchestrator.on_rest_get("/health", HealthResponse)
async def health(ctx: Context) -> HealthResponse:
    return HealthResponse(status="ok")


@orchestrator.on_rest_post("/blend", BlendRequest, BlendResponse)
async def handle_blend(ctx: Context, req: BlendRequest) -> BlendResponse:
    # TODO: Implement the blend endpoint
    # - Use req.user1_token and req.user2_token to fetch tracks
    # - Send to blend_agent for ASI-1 Mini reasoning
    # - Return blended playlist
    return BlendResponse(playlist=[], explanation="TODO: not implemented yet")


@orchestrator.on_message(SharedAgentState)
async def handle_agent_response(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(f"Received state back from agent: session={state.chat_session_id}, result={state.result!r}")
    response = generate_orchestrator_response_from_state(state)
    await ctx.send(
        state.user_sender_address,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=response),
                EndSessionContent(type="end-session"),
            ],
        ),
    )


if __name__ == "__main__":
    orchestrator.run()
