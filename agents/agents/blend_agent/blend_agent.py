from agents.models.config import BLEND_AGENT_SEED
from agents.models.models import SharedAgentState
from uagents import Agent, Context

blend_agent = Agent(
    name="blend_agent",
    seed=BLEND_AGENT_SEED,
    port=8002,
    mailbox=True,
    publish_agent_details=True,
)


def blend_with_asi1(state: SharedAgentState) -> SharedAgentState:
    # TODO: Send track data to ASI-1 Mini for blend analysis
    # - Parse two users' track lists from state.query
    # - Call ASI-1 Mini API to analyze taste overlap
    # - Return blended playlist + explanation in state.result
    state.result = "TODO: asi1 blend reasoning"
    return state


@blend_agent.on_message(SharedAgentState)
async def handle_message(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(f"Received state from orchestrator: session={state.chat_session_id}, query={state.query!r}")
    state = blend_with_asi1(state)
    await ctx.send(sender, state)


if __name__ == "__main__":
    blend_agent.run()
