from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ChatModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        alias_generator=to_camel,
    )


class ChatMessageCreate(ChatModel):
    message: str = Field(min_length=1)


class ChatMessageResponse(ChatModel):
    id: int
    issue_id: int
    sender_id: int
    sender_type: str
    message: str
    created_at: datetime
