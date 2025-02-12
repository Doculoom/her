from typing import List, Optional
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
    text: str = Field(
        description="Memory capturing the essence of the conversation and user details"
    )


class GeneratedMemoryList(BaseModel):
    memories: List[GeneratedMemory] = Field(
        description="List of memories capturing different dimensions"
    )


class UpdatedMemory(BaseModel):
    memory_id: Optional[str] = Field(default=None, description="Optional field")
    updated_memory: str = Field(
        description="Old memory updated with new context or a new memory"
    )


class UpdatedMemoryList(BaseModel):
    updated_memories: List[UpdatedMemory] = Field(
        description="List of updated memories with new context"
    )
