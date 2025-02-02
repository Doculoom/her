from typing import List

from pydantic import BaseModel, Field


class Memory(BaseModel):
    id: str
    user_id: str
    text: str
    model_id: str
    distance: float


class MemoryCreateRequest(BaseModel):
    user_id: str
    text: str


class MemoryUpdateRequest(BaseModel):
    user_id: str
    text: str


class GeneratedMemory(BaseModel):
    """A single generated memory from conversation

    Represents a single memory capturing specific details from the conversation.
    """
    text: str = Field(description="Memory capturing the essence of the conversation and user details")


class GeneratedMemoryList(BaseModel):
    """List of generated memories from conversation.

    Contains multiple memories capturing different dimensions of the conversation.
    """
    memories: List[GeneratedMemory] = Field(description="List of memories capturing different dimensions")


class UpdatedMemory(BaseModel):
    """A single updated memory.

    Represents a memory that has been updated with new context.
    """
    memory_id: str = Field(default=None)
    updated_memory: str = Field(description="Old memory updated with new context or a new memory")


class UpdatedMemoryList(BaseModel):
    """List of updated memories.

    """
    updated_memories: List[UpdatedMemory] = Field(description="List of updated memories with new context")
