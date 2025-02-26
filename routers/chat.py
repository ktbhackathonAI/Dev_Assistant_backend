
from fastapi import APIRouter, Depends
from requests import Session

from dto.chat import ChatRequest, ChatResponse
from db import get_db
from models import Chat


router = APIRouter()

@router.post("/chats/", response_model=ChatResponse)
def create_chat(chat: ChatRequest, db: Session = Depends(get_db)):
    db_chat = Chat(content=chat.content, room_id=chat.room_id)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat