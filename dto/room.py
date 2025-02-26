# ChatRoom DTO
from typing import List
from git import Optional
from pydantic import BaseModel

from dto.chat import ChatResponse


class ChatRoomRequest(BaseModel):
    name: str
    repo_url: str

class ChatRoomResponse(BaseModel):
    id: int
    name: Optional[str] = None
    repo_url: Optional[str] = None
    chats: List[ChatResponse] = []
