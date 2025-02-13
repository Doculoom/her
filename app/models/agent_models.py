from pydantic import BaseModel, Field
from typing import List, TypedDict, Annotated, Optional

from langgraph.graph.message import add_messages


class HerState(TypedDict):
    user_id: str
    user_name: str
    user_channel: str
    next_node: str
    messages: Annotated[List, add_messages]
    context: Optional[str]
    retrieved_memories: Optional[str]


class HerResponse(BaseModel):
    memories_needed: bool = Field(
        description="""Set this field as true if you think you need to fetch more context from the vault
        to respond to the user; If you are able to answer the question set it to false"""
    )
    context: Optional[str] = Field(
        description="""Pass all relevant information needed for the next agent.
        If it is memory agent you should pass a text that will be converted into an embedding and a 
        vector search will be performed to fetch relevant memories.

        Example. If the user with name Vinay is asking about his dog, you response could be "Vinay dog"
        """
    )
    response: Optional[str] = Field(
        description="""Your response to the user based on the message history between you and the user""",
        default=None,
    )


class ChatResponse(BaseModel):
    message: str = Field(description="The message if you want to initiate the chat")
    user_id: str = Field(
        description="The user_id for the user who you want to send the message"
    )
