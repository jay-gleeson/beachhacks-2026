# FETCH-TIFY

An AI-powered multi-agent system that creates personalized Spotify playlists through natural conversation. Built on the Fetch.ai uagents framework, accessible via ASI:One chat.

## How It Works

A user chats with the orchestrator on ASI:One. The orchestrator — powered by an LLM — decides which specialized agents to involve based on the request. Each agent handles one part of the playlist creation process:

```
User: "make me a chill playlist for studying"

Orchestrator (LLM-powered)
    |
    |-- decides: need user's taste --> SpotifyAgent
    |-- decides: analyze taste     --> TasteAgent
    |-- decides: parse request     --> ContextAgent
    |-- decides: find songs        --> DiscoveryAgent
    |-- decides: build playlist    --> PlaylistAgent
    |
    v
User gets a playlist + it's created on their Spotify account
```

The orchestrator doesn't follow a fixed pipeline — it reasons about each request:
- "make me a playlist based on my taste" -> runs all 5 agents
- "give me Frank Ocean and Tyler the Creator songs" -> skips Spotify/Taste, goes straight to Context -> Discovery -> Playlist
- "edm playlist" -> skips Spotify/Taste, searches by genre

## Agents

| Agent | Role | Port |
|-------|------|------|
| **Orchestrator** | LLM-powered router, decides which agents to call and in what order | 8003 |
| **SpotifyAgent** | Fetches user's top 15 artists and top 50 tracks from Spotify | 8004 |
| **TasteAgent** | Uses LLM to analyze the user's listening profile — genres, energy, vibe | 8005 |
| **ContextAgent** | Uses LLM to parse the user's request — mood, activity, genre, artists, playlist name, track count | 8006 |
| **DiscoveryAgent** | Searches Spotify for tracks based on taste + context, with artist-level filtering | 8007 |
| **PlaylistAgent** | Formats the playlist and creates it on the user's Spotify account | 8008 |
| **Auth Server** | Handles per-user Spotify OAuth so each user connects their own account | 9999 |

## Setup

### 1. Prerequisites
- Python 3.12
- A Spotify Developer app (https://developer.spotify.com/dashboard)
- An OpenAI API key
- An Agentverse account (https://agentverse.ai)
- An ASI:One account (https://asi1.ai)

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in your `.env`:
```
ORCHESTRATOR_SEED_PHRASE=<random string>
SPOTIFY_SEED_PHRASE=<random string>
TASTE_SEED_PHRASE=<random string>
CONTEXT_SEED_PHRASE=<random string>
DISCOVERY_SEED_PHRASE=<random string>
PLAYLIST_SEED_PHRASE=<random string>

SPOTIFY_CLIENT_ID=<from Spotify Developer Dashboard>
SPOTIFY_CLIENT_SECRET=<from Spotify Developer Dashboard>
SPOTIFY_REDIRECT_URI=http://127.0.0.1:9999/callback
OPENAI_API_KEY=<your key>
```

### 3. Install dependencies

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r agents/requirements.txt
pip install spotipy openai google-genai
```

### 4. Authenticate with Spotify (first time only)

```bash
.venv/bin/python get_spotify_token.py
```

This opens your browser, you log into Spotify, and the token + refresh token auto-save to `.env`. The refresh token doesn't expire, so future runs auto-refresh without the browser.

### 5. Start all agents

Each agent runs in its own terminal from the project root:

```bash
make orchestrator
make spotify
make taste
make context
make discovery
make playlist
make auth
```

### 6. Connect to ASI:One

1. Open each agent's inspector URL (printed in the terminal when it starts)
2. Click **Connect** on each one
3. Select **Mailbox**
4. On the orchestrator's inspector, click **Go to Agent Profile**
5. Click **Chat with Agent**

## Example Prompts

```
make me a chill playlist for studying
```

```
give me 20 hype workout songs
```

```
create a playlist of Frank Ocean and Tyler the Creator named "vibez"
```

```
edm playlist, 15 songs, named "rave mode"
```

```
generate a sad playlist based on my music taste
```

## Tech Stack

- **Fetch.ai uagents** — agent framework, Agentverse registration, ASI:One chat
- **Spotify Web API** — user profiles, track search, playlist creation
- **OpenAI GPT-4o-mini** — orchestrator routing, taste analysis, context parsing
- **spotipy** — Spotify SDK
- **Python 3.12**

## Architecture Highlights

- **Agentic orchestration**: The orchestrator uses an LLM to decide which agents to call, not a hardcoded pipeline. It can skip agents, and tracks call history to prevent loops.
- **Per-user OAuth**: Each user connects their own Spotify account via the auth server. Tokens are stored per user and auto-refresh.
- **Failsafe design**: Every agent falls back gracefully — expired tokens auto-refresh, API failures fall back to mock data, LLM failures fall back to keyword parsing.
