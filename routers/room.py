from fastapi import APIRouter, Depends, HTTPException
from requests import Session

from dto.room import ChatRoomResponse, ChatRoomRequest
from db import get_db
from models import Chat, ChatRoom


router = APIRouter()

# 채팅방 생성
@router.post("/chat_rooms/", response_model=ChatRoomResponse)
def create_chat_room(chat_room: ChatRoomRequest, db: Session = Depends(get_db)):
    db_chat_room = ChatRoom(name=chat_room.name, repo_url=chat_room.repo_url)
    db.add(db_chat_room)
    db.commit()
    db.refresh(db_chat_room)
    return db_chat_room

# 채팅방 내 모든 대화 내용 조회
@router.get("/chat_rooms/{room_id}/chats", response_model=ChatRoomResponse)
def get_chats_in_room(room_id: int, db: Session = Depends(get_db)):
    db_chats = db.query(Chat).filter(Chat.room_id == room_id).all()
    if not db_chats:
        raise HTTPException(status_code=404, detail="No chats found in this chat room")
    return db_chats