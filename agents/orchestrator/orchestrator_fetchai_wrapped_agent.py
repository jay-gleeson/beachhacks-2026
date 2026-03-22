from datetime import datetime, timezone
from uuid import uuid4

from agents.models.config import (
    ORCHESTRATOR_SEED,
    TASTE_ADDRESS,
    CONTEXT_ADDRESS,
    DISCOVERY_ADDRESS,
    PLAYLIST_ADDRESS,
)
from agents.models.models import SharedAgentState
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

# Pipeline routing: each agent sets pipeline_stage to the next stage
PIPELINE = {
    "taste": TASTE_ADDRESS,
    "context": CONTEXT_ADDRESS,
    "discovery": DISCOVERY_ADDRESS,
    "playlist": PLAYLIST_ADDRESS,
}


class HealthResponse(Model):
    status: str


@orchestrator.on_rest_get("/health", HealthResponse)
async def health(ctx: Context) -> HealthResponse:
    return HealthResponse(status="ok healthy")


@orchestrator.on_message(SharedAgentState)
async def handle_agent_response(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(
        f"Received state: stage={state.pipeline_stage}, session={state.chat_session_id}"
    )

    if state.pipeline_stage == "done":
        # Pipeline complete — send result back to user
        response = generate_orchestrator_response_from_state(state)
        ctx.logger.info("Pipeline complete — sending result to user")
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
    elif state.pipeline_stage in PIPELINE:
        next_addr = PIPELINE[state.pipeline_stage]
        ctx.logger.info(f"Routing to next stage: {state.pipeline_stage}")
        await ctx.send(next_addr, state)
    else:
        ctx.logger.error(f"Unknown pipeline stage: {state.pipeline_stage}")


if __name__ == "__main__":
    orchestrator.run()
