from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base  # Base는 SQLAlchemy의 declarative base로 정의되어 있어야 합니다.
from pydantic import BaseModel
from typing import List, Optional

class ChatRoom(Base):
    __tablename__ = 'chat_room'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    repo_url = Column(String(255))

class Chat(Base):
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    room_id = Column(Integer, ForeignKey('chat_room.id'))

# ChatRoom DTO
class ChatRoomBase(BaseModel):
    name: str
    repo_url: Optional[str] = None  # Optional 필드

class ChatRoomCreate(ChatRoomBase):
    pass

class ChatRoom(ChatRoomBase):
    id: int
    chats: List["Chat"] = []  # 채팅방에 속한 채팅들, 기본 값은 빈 리스트

    class Config:
        orm_mode = True  # SQLAlchemy 모델을 Pydantic 모델로 변환할 수 있게 해줌

# Chat DTO
class ChatBase(BaseModel):
    content: str
    room_id: int

class ChatCreate(ChatBase):
    pass

class Chat(ChatBase):
    id: int

    class Config:
        orm_mode = True  # SQLAlchemy 모델을 Pydantic 모델로 변환할 수 있게 해줌
