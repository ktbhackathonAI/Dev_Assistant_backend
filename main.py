from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from fastapi.middleware.cors import CORSMiddleware
import requests
from pydantic import BaseModel
import openai
from uuid import uuid4
from dotenv import load_dotenv  # dotenv 모듈 임포트

# ✅ 데이터베이스 설정 (기본: SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://jhy:wjdghdus1!@gb-prod.c9wgecae8edg.ap-northeast-2.rds.amazonaws.com:3306/ktbdb")  # MySQL 또는 PostgreSQL로 변경 가능

# ✅ SQLAlchemy 엔진 및 세션 생성
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ SQLAlchemy 모델 기본 클래스
Base = declarative_base()


# .env 파일에서 환경 변수 로드
load_dotenv()

# GITHUB_TOKEN과 GITHUB_USERNAME을 환경 변수로 불러오기
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

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

# ✅ DB 세션을 FastAPI의 Dependency로 제공
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# ✅ 루트 API
@app.get("/")
def root():
    # return {"message": "Welcome to FastAPI Post CRUD API"}
    return {"message": "나 시작했다고"}




# 레포지토리 생성 함수
def create_github_repo(repo_name: str):
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "private": True,  # 개인 레포지토리로 설정
        "description": f"Repository for {repo_name}",
    }

    response = requests.post(url, json=data, headers=headers)

    repo_url = response.json()
    # print(response.json())

    if response.status_code == 201:
        repo_url = response.json()["ssh_url"]
        return {"message": f"Repository '{repo_name}' created successfully!", "repo_url": repo_url}
    else:
        error_message = response.json()["errors"][0]["message"] if "errors" in response.json() else "Failed to create repository"
        raise HTTPException(status_code=response.status_code, detail=error_message)

class RepoCreate(BaseModel):
    repo_name: str

# 레포지토리 생성 API
@app.post("/create-repo/")
async def create_repo(repo: RepoCreate):
    # print(f"Received repo_name: {repo.repo_name}")
    result = create_github_repo(repo.repo_name)
    return result