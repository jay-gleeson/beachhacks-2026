from agents.models.models import SharedAgentState
from agents.spotify.spotify_fetchai_wrapped_agent import spotify_workflow
from agents.context.context_fetchai_wrapped_agent import context_workflow
from agents.discovery.discovery_fetchai_wrapped_agent import discovery_workflow
import json

state = SharedAgentState(chat_session_id="test", query="give me 10 hype songs", user_sender_address="test")
state = spotify_workflow(state)
state = context_workflow(state)
state = discovery_workflow(state)

data = json.loads(state.pipeline_data)
print(f"Mood: {data['context']['mood']}")
print(f"Track count requested: {data['context']['track_count']}")
print(f"\nRecommendations ({len(data['recommendations'])} tracks):")
for i, track in enumerate(data["recommendations"], 1):
    print(f"  {i}. \"{track['title']}\" - {track['artist']} ({track['album']})")
