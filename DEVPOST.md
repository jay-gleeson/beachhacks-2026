# FETCH-TIFY: An AI-Driven Music Discovery Tool

## 🌟 Inspiration

Current workflows for playlist curation are unsatisfying. Here, utilizing a decentralized system of agents, we process a user's idea for a playlist and curate a playlist towards their needs, based off their taste profile. 

## What It Does

FETCH-TIFY is an AI-driven music discovery engine that generates personalized playlists based on user prompts. Users describe their desired mood, context, or vibe, and the system uses an LLM-powered agent orchestrator to interpret intent, analyze user taste preferences via Spotify data, and dynamically generate curated playlists that match their request. The playlist is then added directly to the user's Spotify account.

## 🧠 What We Learned

Building FETCH-TIFY was an adventure in team work, delegation, and logical code construction.

- **Agent Orchestration**: Moving beyond fixed pipelines to an LLM-powered router (GPT-4o-mini) that dynamically decides which agents to invoke based on user intent and gathered data.
- **Spotify API Nuance**: Navigating the complexities of user authorization and rich metadata available through the Spotify Web API.
- **Intent Alignment**: Transforming vague prompts like "cafe lofi music" into structured search parameters, fitting the users' taste, that a discovery engine can use. This became a matter of prompt engineering.

## 🛠️ How We Built It

The project uses a modular, agentic architecture. This is optimal for a team-oriented workflow as well as the debugging process and decentralization:

- **Backend (Python & fetch.ai)**: Specialized agents (Spotify, Taste, Context, Discovery, Playlist) wrapped with the uagents framework.
- **Orchestrator**: An LLM-driven router that manages state transitions and session history.

## 🚧 Challenges We Faced

- **OAuth complexity**: Communicating between uAgents and Spotify API became a challenge. Organizing usage of Spotify's Web API to get a user's tokens was difficult.
- **Debugging and fallback**: Designed fallback mechanisms for failed communication or Spotify account became vital.

## What We're Proud Of

- **Spotify Integration**: Successfully bridged uAgents framework with Spotify's OAuth flow, enabling real-time playlist generation directly to user accounts.
- **Agent Design**: Created a modular agent system that handles distinct tasks (taste analysis, context understanding, discovery) while maintaining clean separation of concerns.
- **End-to-End MVP**: Built a fully functional proof-of-concept that demonstrates the viability of AI-driven playlist curation from concept to deployment with ASI:One.

## What's Next

- **Vercel deployment**: Format and build an in-depth front-end with a chat interface, that outputs your playlist on an embedded player, as well as on your account.
- **Further customization**: While current project allows for a variety of moods and song customization, further customization of the playlist like photo and description would make a smoother user experience.