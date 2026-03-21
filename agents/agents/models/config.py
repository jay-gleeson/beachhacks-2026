import os
from dotenv import find_dotenv, load_dotenv
from uagents_core.identity import Identity

load_dotenv(find_dotenv())

SPOTIFY_AGENT_SEED = os.getenv("SPOTIFY_AGENT_SEED_PHRASE")
BLEND_AGENT_SEED = os.getenv("BLEND_AGENT_SEED_PHRASE")
ORCHESTRATOR_SEED = os.getenv("ORCHESTRATOR_SEED_PHRASE")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
ASI1_API_KEY = os.getenv("ASI1_API_KEY")

SPOTIFY_AGENT_ADDRESS = Identity.from_seed(seed=SPOTIFY_AGENT_SEED, index=0).address
BLEND_AGENT_ADDRESS = Identity.from_seed(seed=BLEND_AGENT_SEED, index=0).address
