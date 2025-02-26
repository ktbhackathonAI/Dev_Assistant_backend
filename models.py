from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base  # Base는 SQLAlchemy의 declarative base로 정의되어 있어야 합니다.

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
