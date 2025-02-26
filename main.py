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
import git
import base64

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

    # repo_url = response.json()
    # print(response.json())

    if response.status_code == 201:
        repo_url = response.json()["ssh_url"]
        return {"message": f"Repository '{repo_name}' created successfully!", "repo_url": repo_url}
    else:
        error_message = response.json()["errors"][0]["message"] if "errors" in response.json() else "Failed to create repository"
        raise HTTPException(status_code=response.status_code, detail=error_message)



def get_all_files(directory: str):
    return [
        (os.path.join(directory, file), file)  # (전체 경로, 파일명)
        for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))
    ]

# 특정 파일을 GitHub 레포지토리에 업로드
def push_skeleton_file_to_repo(repo_name: str, file_path: str, relative_path: str):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/contents/{relative_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 파일을 읽고 Base64로 인코딩
    with open(file_path, "rb") as file:
        encoded_content = base64.b64encode(file.read()).decode()

    data = {
        "message": f"Add {relative_path}",
        "content": encoded_content,
        "branch": "main"
    }

    response = requests.put(url, json=data, headers=headers)

    if response.status_code in [200, 201]:
        return {"message": f"File '{relative_path}' uploaded successfully!"}
    else:
        error_message = response.json().get("message", "Failed to upload file")
        raise HTTPException(status_code=response.status_code, detail=error_message)




class RepoCreate(BaseModel):
    repo_name: str

# 레포지토리 생성 API
@app.post("/create-repo/")
async def create_repo(repo: RepoCreate):
    # print(f"Received repo_name: {repo.repo_name}")
    result = create_github_repo(repo.repo_name)
    return result


# 현재 작업 중인 프로젝트의 루트 디렉토리
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# print(f"project_root: {PROJECT_ROOT}")

# 스켈레톤 파일이 저장된 기본 폴더 (프로젝트 내부)
SKELETONS_DIR = os.path.join(PROJECT_ROOT, "skeletons")
# print(f"skeletons_dir: {SKELETONS_DIR}")


# 파일 푸시 API
@app.post("/push-files/")
async def push_skeleton_files(request: RepoCreate):
    """
    로컬 디렉터리 내 모든 파일을 GitHub 레포지토리에 푸시
    """
    repo_name = request.repo_name
    
    if not os.path.exists(SKELETONS_DIR):
        raise HTTPException(status_code=400, detail=f"Skeleton directory '{repo_name}' does not exist in '{SKELETONS_DIR}'")

    # 모든 파일 경로 가져오기
    files = get_all_files(SKELETONS_DIR)
    # print(f"files in push-files method: {files}")

    results = {}
    for full_path, relative_path in files:
        try:
            results[relative_path] = push_skeleton_file_to_repo(repo_name, full_path, relative_path)
        except HTTPException as e:
            results[relative_path] = {"error": str(e.detail)}

    return {"results": results}