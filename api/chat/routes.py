from fastapi import APIRouter, Depends, HTTPException  # FastAPI 관련 모듈 임포트
from sqlalchemy.orm import Session  # SQLAlchemy 세션 관리
from core.database import get_db  # 데이터베이스 연결 함수
from core.models import ChatRoom, Message  # DB 모델 임포트
from core.config import settings  # 환경 변수 설정 모듈
import aiohttp  # 비동기 HTTP 요청 처리
from pydantic import BaseModel  # Pydantic 모델 정의를 위한 모듈 임포트

# API 라우터 객체 생성: '/chat' 접두어 하위에 엔드포인트 정의
router = APIRouter()
# Pydantic 모델 정의: 메시지 생성 요청 본문 검증용
class MessageCreate(BaseModel):
    content: str  # 메시지 내용, 필수 필드

@router.post("/rooms")  # POST 요청을 '/chat/rooms' 경로로 처리
def create_chat_room(repo_url: str = None, db: Session = Depends(get_db)):
    """새로운 채팅 룸을 생성합니다.

    Args:
        repo_url (str, optional): 연관된 GitHub 리포지토리 URL, 선택적.
        db (Session): 데이터베이스 세션.

    Returns:
        dict: 생성된 채팅 룸의 ID.
    """
    chat_room = ChatRoom(repo_url=repo_url)  # 새 ChatRoom 객체 생성
    db.add(chat_room)  # DB에 추가
    db.commit()  # 변경 사항 커밋
    db.refresh(chat_room)  # 생성된 객체 새로고침 (ID 반영)
    return {"room_id": chat_room.id}

@router.get("/rooms")  # GET 요청을 '/chat/rooms' 경로로 처리
def get_chat_rooms(db: Session = Depends(get_db)):
    """모든 채팅 룸 목록을 반환합니다.

    Args:
        db (Session): 데이터베이스 세션.

    Returns:
        list: 채팅 룸 목록 (ID, repo_url, 생성 시간 포함).
    """
    chat_rooms = db.query(ChatRoom).all()  # 모든 채팅 룸 조회
    rooms_list = [
        {
            "room_id": room.id,
            "repo_url": room.repo_url,
            "created_at": room.created_at.isoformat()
        }
        for room in chat_rooms
    ]
    return rooms_list

@router.delete("/rooms/{room_id}")  # DELETE 요청을 '/chat/rooms/{room_id}' 경로로 처리
def delete_chat_room(room_id: int, db: Session = Depends(get_db)):
    """지정된 채팅 룸을 삭제합니다.

    Args:
        room_id (int): 삭제할 채팅 룸의 ID.
        db (Session): 데이터베이스 세션.

    Returns:
        dict: 삭제 성공 메시지.

    Raises:
        HTTPException: 룸이 존재하지 않을 경우 404 반환.
    """
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    db.delete(room)
    db.commit()
    return {"message": "Room deleted"}

@router.post("/rooms/{room_id}/messages")
async def send_message(room_id: int, message: MessageCreate, db: Session = Depends(get_db)):
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    # 사용자 메시지 저장
    user_msg = Message(chat_room_id=room_id, content=message.content, is_system=0)
    db.add(user_msg)
    db.commit()

    # 시스템 응답 메시지 저장
    system_msg = Message(chat_room_id=room_id, content=f"System: {message.content}", is_system=1)
    db.add(system_msg)
    db.commit()

    # 프론트엔드로 알림 전송
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"{settings.FRONTEND_URL}/notify",
            json={"room_id": room_id, "message": system_msg.content}
        )

    # 배열 형태로 메시지 반환
    return [
        {"text": user_msg.content, "sender": "user"},
        {"text": system_msg.content, "sender": "system"}
    ]

@router.get("/rooms/{room_id}/messages")  # GET 요청을 '/chat/rooms/{room_id}/messages' 경로로 처리
def get_chat_room_messages(room_id: int, db: Session = Depends(get_db)):
    """지정된 채팅 룸의 기존 대화 내역을 반환합니다.

    Args:
        room_id (int): 대화 내역을 조회할 채팅 룸의 ID.
        db (Session): 데이터베이스 세션.

    Returns:
        list: 메시지 목록 (ID, 내용, 시스템 여부, 생성 시간 포함).

    Raises:
        HTTPException: 룸이 존재하지 않을 경우 404 반환.
    """
    # 채팅 룸 존재 여부 확인
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    # 해당 룸의 모든 메시지 조회
    messages = db.query(Message).filter(Message.chat_room_id == room_id).all()

    # 반환할 데이터 형식으로 변환
    messages_list = [
        {
            "message_id": msg.id,
            "content": msg.content,
            "is_system": bool(msg.is_system),  # 0/1을 Boolean으로 변환
            "created_at": msg.created_at.isoformat()  # ISO 형식으로 시간 변환
        }
        for msg in messages
    ]

    return messages_list
