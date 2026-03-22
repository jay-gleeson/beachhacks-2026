from agents.context.context_fetchai_wrapped_agent import context_workflow
from agents.models.models import SharedAgentState
import json

queries = [
    "make me a chill playlist for studying",
    "I need hype workout songs",
    "give me 15 sad tracks",
    "something heavy and aggressive",
    "romantic date night vibes",
    "5 songs for a road trip",
]

for q in queries:
    state = SharedAgentState(chat_session_id="t", query=q, user_sender_address="t")
    state = context_workflow(state)
    ctx = json.loads(state.pipeline_data)["context"]
    print(f"{q!r}")
    print(f"  mood={ctx['mood']}, activity={ctx['activity']}, tracks={ctx['track_count']}")
    print()
