from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import Message
from core.config import settings
import aiohttp
import os

# API 라우터 객체 생성: '/ai' 경로 하위에 엔드포인트 정의
router = APIRouter()

# 채팅 룸 대화를 AI 서버로 내보내고 처리 결과를 저장하는 엔드포인트
@router.get("/rooms/{room_id}/export")
async def export_to_ai(room_id: int, db: Session = Depends(get_db)):
    # 지정된 채팅 룸의 모든 메시지 조회
    messages = db.query(Message).filter(Message.chat_room_id == room_id).all()
    if not messages:
        # 메시지가 없으면 404 에러 발생
        raise HTTPException(status_code=404, detail="No messages found")

    # 메시지를 JSON 형식으로 변환
    conversation = [{"content": m.content, "is_system": m.is_system} for m in messages]

    # AI LangChain 서버로 비동기 요청 전송
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{settings.AI_LANGCHAIN_URL}/process", json=conversation) as resp:
            ai_response = await resp.json()  # AI 서버 응답 받기

    # AI 응답을 파일로 저장
    file_name = f"ai_response_{room_id}.json"
    with open(file_name, "w") as f:
        f.write(str(ai_response))  # 응답을 문자열로 저장

    # 성공 메시지와 파일 이름 반환
    return {"message": "Exported and processed by AI", "file": file_name}
