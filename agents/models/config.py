import os
from dotenv import find_dotenv, load_dotenv
from uagents_core.identity import Identity

load_dotenv(find_dotenv())

ORCHESTRATOR_SEED = os.getenv("ORCHESTRATOR_SEED_PHRASE")
SPOTIFY_SEED = os.getenv("SPOTIFY_SEED_PHRASE")
TASTE_SEED = os.getenv("TASTE_SEED_PHRASE")
CONTEXT_SEED = os.getenv("CONTEXT_SEED_PHRASE")
DISCOVERY_SEED = os.getenv("DISCOVERY_SEED_PHRASE")
PLAYLIST_SEED = os.getenv("PLAYLIST_SEED_PHRASE")

SPOTIFY_TOKEN = os.getenv("SPOTIFY_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SPOTIFY_ADDRESS = Identity.from_seed(seed=SPOTIFY_SEED, index=0).address
TASTE_ADDRESS = Identity.from_seed(seed=TASTE_SEED, index=0).address
CONTEXT_ADDRESS = Identity.from_seed(seed=CONTEXT_SEED, index=0).address
DISCOVERY_ADDRESS = Identity.from_seed(seed=DISCOVERY_SEED, index=0).address
PLAYLIST_ADDRESS = Identity.from_seed(seed=PLAYLIST_SEED, index=0).address
