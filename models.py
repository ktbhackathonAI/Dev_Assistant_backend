from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base  # Base는 SQLAlchemy의 declarative base로 정의되어 있어야 합니다.

class ChatRoom(Base):
    __tablename__ = 'chat_room'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    repo_url = Column(String(255))

    # 관계 정의 (반대 방향)
    chats = relationship("Chat", back_populates="room")

    def __repr__(self):
        return f"<ChatRoom(id={self.id}, name={self.name})>"

class Chat(Base):
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    room_id = Column(Integer, ForeignKey('chat_room.id'))

    # 관계 정의 (반대 방향)
    room = relationship("ChatRoom", back_populates="chats")

    def __repr__(self):
        return f"<Chat(id={self.id}, content={self.content})>"
