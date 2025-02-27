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
        {"room_id": room.id, "name": room.name, "repo_url": room.repo_url, "created_at": room.created_at.isoformat()}
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
    """대화 방의 정보와 기존 대화 내역을 가져와 process-test에 전달하고, 스트리밍 응답을 반환합니다.

    Args:
        room_id (int): 대화 방 ID
        message (MessageCreate): 전송할 메시지 데이터
        db (Session): DB 세션

    Returns:
        StreamingResponse: process-test에서 받은 스트리밍 응답
    """
    # 1. 대화 방 정보 가져오기
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")

    # 2. 해당 대화 방의 기존 메시지 내역 가져오기
    messages = db.query(Message).filter(Message.chat_room_id == room_id).order_by(Message.created_at.asc()).all()
    message_history = [{"content": msg.content, "sender": "system" if bool(msg.is_system) else "user", "created_at": msg.created_at.isoformat()} for msg in messages]

    # 3. POST 요청에 보낼 데이터 구성
    payload = {
        "room": {
            "id": room.id,
            "name": room.name,  # Room 모델에 name 필드가 있다고 가정
            "created_at": room.created_at.isoformat() if room.created_at else None
        },
        "message_history": message_history,
        "new_message": {
            "content": message.content,
            "role": "user"  # 새 메시지는 사용자 메시지로 가정
        }
    }
    # 4. AI_LANGCHAIN_URL/process-test/에 POST 요청 보내기
    async def stream_from_process_test():
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(PROCESS_TEST_URL, json=payload) as resp:
                    if resp.status != 200:
                        raise HTTPException(status_code=resp.status, detail="Failed to connect to process-test endpoint")

                    # 스트리밍 응답을 그대로 클라이언트에 전달
                    async for chunk in resp.content.iter_any():
                        yield chunk.decode('utf-8')  # 바이트를 문자열로 디코딩하여 전달
            except aiohttp.ClientError as e:
                yield f"data: Error connecting to process-test: {str(e)}\n\n"

    # 5. StreamingResponse로 스트리밍 반환
    return StreamingResponse(stream_from_process_test(), media_type="text/event-stream")

@router.get("/rooms/{room_id}/messages")
def get_chat_room_messages(room_id: int, db: Session = Depends(get_db)):
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    messages = db.query(Message).filter(Message.chat_room_id == room_id).all()
    messages_list = [
        {"message_id": msg.id, "content": msg.content, "sender": "system" if bool(msg.is_system) else "user", "is_system": bool(msg.is_system), "created_at": msg.created_at.isoformat()}
        for msg in messages
    ]
    print(messages_list)
    return messages_list
