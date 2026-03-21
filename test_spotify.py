from agents.models.models import SharedAgentState
from agents.spotify.spotify_fetchai_wrapped_agent import spotify_workflow
import json

state = SharedAgentState(chat_session_id="test", query="chill vibes", user_sender_address="test")
state = spotify_workflow(state)
print("Stage:", state.pipeline_stage)
print("Data:", json.dumps(json.loads(state.pipeline_data), indent=2))
