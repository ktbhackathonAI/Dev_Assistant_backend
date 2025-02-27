from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import ChatRoom, Message
from pydantic import BaseModel
from dotenv import load_dotenv
import asyncio
import json
import aiohttp
import os
from datetime import datetime
import requests
import base64

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 AI_LANGCHAIN_URL 가져오기
AI_LANGCHAIN_URL = os.getenv("AI_LANGCHAIN_URL", "http://localhost:8001")  # 기본값 설정
GENERATE_CODE_URL = f"{AI_LANGCHAIN_URL}/generate-code/"  # 최종 URL 구성

# 환경 변수에서 URL과 토큰 가져오기
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# GitHub API 기본 URL
GITHUB_API_URL = "https://api.github.com"

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

# 4. 스트리밍 응답 처리
@router.post("/rooms/{room_id}/messages")
async def send_message(room_id: int, message: MessageCreate, db: Session = Depends(get_db)):
    """대화 방의 정보와 기존 대화 내역을 generate-code에 전달하고, 결과를 처리 후 스트리밍 반환.

    Args:
        room_id (int): 대화 방 ID
        message (MessageCreate): 전송할 메시지 데이터
        db (Session): DB 세션

    Returns:
        StreamingResponse: 처리 결과에 따른 스트리밍 응답
    """
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not found in .env file")

    # 1. 대화 방 정보 가져오기
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")

    # 2. 해당 대화 방의 기존 메시지 내역 가져오기
    messages = db.query(Message).filter(Message.chat_room_id == room_id).order_by(Message.created_at.asc()).all()
    message_history = [{"content": msg.content, "sender": "system" if bool(msg.is_system) else "user", "created_at": msg.created_at.isoformat()} for msg in messages]

    user_message = Message(
        chat_room_id=room.id,
        content=message.content,
        is_system=0,
        created_at=datetime.utcnow()
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # 3. POST 요청에 보낼 데이터 구성
    payload = {
        "room": {
            "id": room.id,
            "name": room.name,
            "created_at": room.created_at.isoformat() if room.created_at else None
        },
        "message_history": message_history,
        "new_message": {
            "content": message.content,
            "role": "user"
        }
    }

    # generate-code API 호출
    async with aiohttp.ClientSession() as session:
        async with session.post(GENERATE_CODE_URL, json=payload) as resp:

            if resp.status != 200:
                error_detail = await resp.text()
                raise HTTPException(status_code=resp.status, detail=f"Failed to connect to generate-code: {error_detail}")

            # JSON 응답 처리
            response_data = await resp.json()

            if not isinstance(response_data, dict) or len(response_data) == 0:
                raise HTTPException(status_code=500, detail="Invalid response format from generate-code")

            key = next(iter(response_data))
            value = response_data[key]


            print(response_data)
            # moreinfo 경우: 바로 반환
            if key == "Sub_question":
                user_message = Message(
                    chat_room_id=room.id,
                    content=value,
                    is_system=1,
                    created_at=datetime.utcnow()
                )
                db.add(user_message)
                db.commit()
                db.refresh(user_message)
                return {"message": value}

            # makecode 경우: 스트리밍으로 GitHub 처리
            elif key == "project_folder_list":
                filelist = value
                repo_name = f"auto-repo-{room_id}"
                # print("파일제작")
                # print("filelist")
                # print(filelist)
                # print("repo_name")
                # print(repo_name)

                async def stream_github_process():
                    yield "data: Starting GitHub repository creation\n\n"

                    # GitHub 사용자 이름 가져오기
                    headers = {
                        "Authorization": f"token {GITHUB_TOKEN}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                    user_resp = requests.get(f"{GITHUB_API_URL}/user", headers=headers)
                    if user_resp.status_code != 200:
                        yield f"data: Error: Failed to get GitHub user info - {user_resp.text}\n\n"
                        return
                    username = user_resp.json()["login"]

                    # 리포지토리 생성
                    create_url = f"{GITHUB_API_URL}/user/repos"
                    create_payload = {
                        "name": repo_name,
                        "private": False,
                        "description": f"Auto-generated repo for room {room_id}"
                    }
                    create_resp = requests.post(create_url, json=create_payload, headers=headers)
                    if create_resp.status_code != 201:
                        yield f"data: Error: Failed to create repository - {create_resp.text}\n\n"
                        return
                    yield f"data: Repository '{repo_name}' created successfully for user '{username}'\n\n"

                    # 파일 커밋 시작
                    yield "data: Starting file commit process\n\n"
                    for file_path in filelist:
                        if not os.path.exists(file_path):
                            yield f"data: Error: File '{file_path}' does not exist\n\n"
                            continue

                        with open(file_path, "rb") as f:
                            content = f.read()
                        encoded_content = base64.b64encode(content).decode()

                        commit_url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}/contents/{os.path.basename(file_path)}"
                        commit_payload = {
                            "message": f"Add {os.path.basename(file_path)} via API",
                            "content": encoded_content,
                            "branch": "main"
                        }
                        commit_resp = requests.put(commit_url, json=commit_payload, headers=headers)
                        if commit_resp.status_code not in (200, 201):
                            yield f"data: Error committing '{file_path}': {commit_resp.text}\n\n"
                            continue
                        yield f"data: Successfully committed '{file_path}' to '{repo_name}'\n\n"

                    yield "data: File commit process completed\n\n"

                return StreamingResponse(stream_github_process(), media_type="text/event-stream")

            else:
                raise HTTPException(status_code=400, detail=f"Unknown response key: {key}")


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
    # print(messages_list)
    return messages_list
