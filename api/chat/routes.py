from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import ChatRoom, Message
from pydantic import BaseModel
import asyncio
import json

router = APIRouter()

class MessageCreate(BaseModel):
    content: str

@router.post("/rooms")
def create_chat_room(repo_url: str = None, db: Session = Depends(get_db)):
    chat_room = ChatRoom(repo_url=repo_url)
    db.add(chat_room)
    db.commit()
    db.refresh(chat_room)
    return {"room_id": chat_room.id}

@router.get("/rooms")
def get_chat_rooms(db: Session = Depends(get_db)):
    chat_rooms = db.query(ChatRoom).all()
    rooms_list = [
        {"room_id": room.id, "repo_url": room.repo_url, "created_at": room.created_at.isoformat()}
        for room in chat_rooms
    ]
    return rooms_list

@router.delete("/rooms/{room_id}")
def delete_chat_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    db.delete(room)
    db.commit()
    return {"message": "Room deleted"}

@router.post("/rooms/{room_id}/messages")
async def send_message(room_id: int, message: MessageCreate, db: Session = Depends(get_db)):
    """채팅 룸에 메시지를 전송하고 시스템 응답 제작 과정을 스트리밍합니다."""
    # 채팅 룸 확인
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    # 사용자 메시지 저장 및 내용 복사
    user_msg = Message(chat_room_id=room_id, content=message.content, is_system=0)
    db.add(user_msg)
    db.commit()
    user_content = user_msg.content  # 세션 외부 변수로 복사

    # 시스템 응답 준비
    system_response = f"System: {message.content}"

    async def message_stream():
        # 사용자 메시지 전송 (복사된 데이터 사용)
        yield json.dumps({"content": user_content, "sender": "user", "status": "completed"}) + "\n"

        # 시스템 응답 제작 과정 시뮬레이션
        system_response_parts = ["System: ", message.content[:len(message.content)//2], message.content]
        current_response = ""

        for i, part in enumerate(system_response_parts):
            current_response += part
            status = "processing" if i < len(system_response_parts) - 1 else "completed"
            yield json.dumps({"content": current_response, "sender": "system", "status": status}) + "\n"
            await asyncio.sleep(5)

        # 스트리밍 완료 후 시스템 메시지 저장
        if current_response == system_response:
            system_msg = Message(chat_room_id=room_id, content=current_response, is_system=1)
            db.add(system_msg)
            db.commit()

    return StreamingResponse(message_stream(), media_type="application/x-ndjson")

@router.get("/rooms/{room_id}/messages")
def get_chat_room_messages(room_id: int, db: Session = Depends(get_db)):
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    messages = db.query(Message).filter(Message.chat_room_id == room_id).all()
    messages_list = [
        {"message_id": msg.id, "content": msg.content, "is_system": bool(msg.is_system), "created_at": msg.created_at.isoformat()}
        for msg in messages
    ]
    return messages_list
