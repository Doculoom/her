from pydantic import BaseModel


class TaskMessage(BaseModel):
    user_id: str
    channel_type: str
    channel_id: str
    text: str
