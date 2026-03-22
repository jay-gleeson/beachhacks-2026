.PHONY: orchestrator spotify taste context discovery playlist auth

orchestrator:
	PYTHONPATH=agents .venv/bin/python -m agents.orchestrator.orchestrator_fetchai_wrapped_agent

spotify:
	PYTHONPATH=agents .venv/bin/python -m agents.spotify.spotify_fetchai_wrapped_agent

taste:
	PYTHONPATH=agents .venv/bin/python -m agents.taste.taste_fetchai_wrapped_agent

context:
	PYTHONPATH=agents .venv/bin/python -m agents.context.context_fetchai_wrapped_agent

discovery:
	PYTHONPATH=agents .venv/bin/python -m agents.discovery.discovery_fetchai_wrapped_agent

playlist:
	PYTHONPATH=agents .venv/bin/python -m agents.playlist.playlist_fetchai_wrapped_agent

auth:
	.venv/bin/python spotify_auth_server.py
