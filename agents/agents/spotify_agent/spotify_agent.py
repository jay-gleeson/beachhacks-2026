from agents.models.config import SPOTIFY_AGENT_SEED
from agents.models.models import SharedAgentState
from uagents import Agent, Context

spotify_agent = Agent(
    name="spotify_agent",
    seed=SPOTIFY_AGENT_SEED,
    port=8001,
    mailbox=True,
    publish_agent_details=True,
)


def fetch_top_tracks(state: SharedAgentState) -> SharedAgentState:
    # TODO: Call Spotify Web API to get top tracks for a user
    # - Parse token from state.query
    # - GET /v1/me/top/tracks
    # - Write results to state.result
    state.result = "TODO: spotify top tracks"
    return state


@spotify_agent.on_message(SharedAgentState)
async def handle_message(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(f"Received state from orchestrator: session={state.chat_session_id}, query={state.query!r}")
    state = fetch_top_tracks(state)
    await ctx.send(sender, state)


if __name__ == "__main__":
    spotify_agent.run()
