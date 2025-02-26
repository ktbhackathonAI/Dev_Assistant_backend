from sqlalchemy import Column, Integer, String, Text, ForeignKey
from db import Base

class ChatRoom(Base):
    __tablename__ = 'chat_room'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    repo_url = Column(String(255))

class Chat(Base):
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String(255))
    room_id = Column(Integer)