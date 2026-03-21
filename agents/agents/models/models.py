from uagents import Model


class TrackInfo(Model):
    name: str
    artist: str
    uri: str


class SharedAgentState(Model):
    chat_session_id: str
    query: str
    user_sender_address: str
    result: str = ""


class BlendRequest(Model):
    user1_token: str
    user2_token: str


class BlendResponse(Model):
    playlist: list[TrackInfo]
    explanation: str
