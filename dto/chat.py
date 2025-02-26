# Chat DTO
from pydantic import BaseModel


class ChatRequest(BaseModel):
    content: str
    room_id: int

class ChatResponse(BaseModel):
    id: int
    content: str
    room_id: int
