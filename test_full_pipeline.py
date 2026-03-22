from agents.models.models import SharedAgentState
from agents.spotify.spotify_fetchai_wrapped_agent import spotify_workflow
from agents.taste.taste_fetchai_wrapped_agent import taste_workflow
from agents.context.context_fetchai_wrapped_agent import context_workflow
from agents.discovery.discovery_fetchai_wrapped_agent import discovery_workflow
from agents.playlist.playlist_fetchai_wrapped_agent import playlist_workflow

query = "make me a chill playlist for studying"

print(f"Query: {query!r}\n")
print("=" * 50)

state = SharedAgentState(chat_session_id="test", query=query, user_sender_address="test")

print("[1/5] SpotifyAgent...")
state = spotify_workflow(state)

print("[2/5] TasteAgent...")
state = taste_workflow(state)

print("[3/5] ContextAgent...")
state = context_workflow(state)

print("[4/5] DiscoveryAgent...")
state = discovery_workflow(state)

print("[5/5] PlaylistAgent...")
state = playlist_workflow(state)

print("=" * 50)
print()
print(state.result)
