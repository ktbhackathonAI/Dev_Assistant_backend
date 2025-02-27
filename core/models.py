from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from core.database import Base
from datetime import datetime

# 채팅 룸 테이블 정의
class ChatRoom(Base):
    __tablename__ = "chat_rooms"  # 테이블 이름
    id = Column(Integer, primary_key=True, index=True)  # 고유 식별자, 인덱스 적용
    name = Column(String(255), nullable=True)      # 채팅방 이름, 선택적
    repo_url = Column(String(255), nullable=True)       # GitHub 리포지토리 URL, 선택적
    created_at = Column(DateTime, default=datetime.utcnow)  # 생성 시간, 기본값 UTC 현재 시간

# 메시지 테이블 정의
class Message(Base):
    __tablename__ = "messages"  # 테이블 이름
    id = Column(Integer, primary_key=True, index=True)  # 고유 식별자, 인덱스 적용
    chat_room_id = Column(Integer, ForeignKey("chat_rooms.id"))  # 외래 키, ChatRoom 참조
    content = Column(String(500))  # 메시지 내용, 최대 500자
    is_system = Column(Integer, default=0)  # 0: 사용자 메시지, 1: 시스템 메시지
    created_at = Column(DateTime, default=datetime.utcnow)  # 생성 시간, 기본값 UTC 현재 시간
