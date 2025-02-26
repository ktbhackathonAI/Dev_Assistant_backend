from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

from fastapi.middleware.cors import CORSMiddleware
import openai
from dotenv import load_dotenv  # dotenv 모듈 임포트

from typing import List
from routers import github, chat, room

# .env 파일에서 환경 변수 로드
load_dotenv()

openai.api_key = 'YOUR_OPENAI_API_KEY'  # OpenAI API 키

# ✅ FastAPI 앱 생성
app = FastAPI(root_path="/api")

# CORS 설정
origins = [
    "http://localhost:3000",  # React 개발 서버 URL
    "http://127.0.0.1:3000",  # React 개발 서버 URL (다른 포트에 접근할 때 필요할 수 있음)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 출처
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# ✅ 루트 API
@app.get("/")
def root():
    # return {"message": "Welcome to FastAPI Post CRUD API"}
    return {"message": "나 시작했다고"}

app.include_router(github.router)
app.include_router(room.router)
app.include_router(chat.router)