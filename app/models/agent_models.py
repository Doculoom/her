from pydantic import BaseModel, Field
from typing import List, TypedDict, Annotated, Optional

from langgraph.graph.message import add_messages


class HerResponse(BaseModel):
    memories_needed: bool = Field(
        description=(
            "True if you need to fetch user memories from the vault; "
            "False if you can answer without additional context."
        )
    )
    context: Optional[str] = Field(
        description=(
            "Information for the next agent.\n\n"
            "f the next agent is the MemoryAgent → provide a short phrase to embed for vector search "
            '(e.g., "Vinay dog").\n\n'
            "If the next agent is the SearchAgent** → include:\n"
            " 1. Conversational context (why the user is asking).\n"
            " 2. Any relevant user memories or preferences.\n"
            " 3. Tone / style hints so the reply feels like a human friend.\n\n"
            "Example for SearchAgent:\n"
            '"User name: <Name>.  He’s been tracking Tesla stock all week and is excited when it’s up. '
            "Explain the price in a friendly, concise tone and the reason why it went up. If TSLA is up, congratulate "
            "him with something like"
            "'Nice! Looks like good new for <Vinay> Tesla’s having a good day 🚀'. "
            'If it’s down, empathize gently."\n'
        )
    )
    response: Optional[str] = Field(
        default=None,
        description="Your direct reply to the user if no further agents are needed.",
    )
    search_needed: bool = Field(
        default=False,
        description=(
            "True ONLY if you need live internet data; otherwise leave false."
        ),
    )
    search_query: Optional[str] = Field(
        description=(
            "Best Google search query to feed to the SearchAgent when search_needed=true."
        )
    )


class ChatResponse(BaseModel):
    response: str = Field(description="The message if you want to initiate the chat")
    initiate_chat: bool = Field(
        description="Boolean indicating if the agent wants to initiated the chat with the user"
    )
    context: Optional[str] = Field(
        description=(
            "Information for the next agent.\n\n"
            "f the next agent is the MemoryAgent → provide a short phrase to embed for vector search "
            '(e.g., "Vinay dog").\n\n'
            "If the next agent is the SearchAgent** → include:\n"
            " 1. Conversational context (why the user is asking).\n"
            " 2. Any relevant user memories or preferences.\n"
            " 3. Tone / style hints so the reply feels like a human friend.\n\n"
            "Example for SearchAgent:\n"
            '"User name: <Name>.  He’s been tracking Tesla stock all week and is excited when it’s up. '
            "Explain the price in a friendly, concise tone and the reason why it went up. If TSLA is up, congratulate "
            "him with something like"
            "'Nice! Looks like good new for <Vinay> Tesla’s having a good day 🚀'. "
            'If it’s down, empathize gently."\n'
        )
    )
    search_needed: bool = Field(
        default=False,
        description=(
            "True ONLY if you need live internet data; otherwise leave false."
        ),
    )
    search_query: Optional[str] = Field(
        description=(
            "Best Google search query to feed to the SearchAgent when search_needed=true."
        )
    )


class AgentState(TypedDict):
    user_id: str
    user_name: str
    user_channel: str
    next_node: str
    messages: Annotated[List, add_messages]
    context: Optional[str]
    search_query: Optional[str]
    search_needed: bool
    response: Optional[str]


class HerState(AgentState):
    retrieved_memories: Optional[str]


class ChatAgentState(AgentState):
    initiate_chat: bool
    inactive_message_sent: bool
