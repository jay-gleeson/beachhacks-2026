from agents.models.models import SharedAgentState
from agents.spotify.spotify_fetchai_wrapped_agent import spotify_workflow
from agents.taste.taste_fetchai_wrapped_agent import taste_workflow
import json

state = SharedAgentState(chat_session_id="test", query="chill vibes", user_sender_address="test")
state = spotify_workflow(state)
state = taste_workflow(state)
print(json.dumps(json.loads(state.pipeline_data)["taste_profile"], indent=2))
