import base64
import os
from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import requests
from pydantic import BaseModel
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# GitHub API 기본 URL 및 토큰 설정
GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # .env에서 GITHUB_TOKEN 가져오기

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 파일이 저장된 기본 디렉토리 (app/data/generate_projects)
BASE_DIR = os.path.join(PROJECT_ROOT, "app", "data", "generate_projects")

# API 라우터 객체 생성
router = APIRouter()

# 요청 데이터 모델 정의
class RepoPushRequest(BaseModel):
    repo_name: str     # 생성할 리포지토리 이름
    file_paths: List[str]  # 커밋할 파일 이름 배열 (예: ["file1.txt", "file2.py"])

class FileCheckRequest(BaseModel):
    repo_name: str     # 확인할 리포지토리 이름
    file_paths: List[str]  # 확인할 파일 이름 배열

# 파일 존재 여부 테스트용 API
@router.post("/check-files/")
async def check_files(request: FileCheckRequest):
    """지정된 파일들이 로컬 디렉토리에 존재하는지 확인하는 API.

    Args:
        request (FileCheckRequest): 리포지토리 이름, 파일 이름 배열.

    Returns:
        StreamingResponse: 파일 존재 여부를 스트림으로 반환.
    """
    repo_name = request.repo_name
    file_names = request.file_paths

    # 프로젝트 디렉토리 경로
    project_dir = os.path.join(BASE_DIR, repo_name)

    # 스트림으로 파일 존재 여부를 반환하는 제너레이터
    async def event_stream():
        yield "data: Starting file existence check\n\n"

        # 프로젝트 디렉토리 확인
        if not os.path.exists(project_dir):
            yield f"data: Error: Project directory '{project_dir}' does not exist\n\n"
            yield "data: Check completed with errors\n\n"
            return

        # 파일 존재 여부 확인
        for file_name in file_names:
            file_path = os.path.join(project_dir, file_name)
            if os.path.exists(file_path):
                yield f"data: File '{file_name}' exists at '{file_path}'\n\n"
            else:
                yield f"data: File '{file_name}' does not exist at '{file_path}'\n\n"

        yield "data: Check completed\n\n"

    # StreamingResponse로 이벤트 스트림 반환
    return StreamingResponse(event_stream(), media_type="text/event-stream")

# GitHub 리포지토리 생성 및 파일 푸시 API
@router.post("/push-to-new-repo/")
async def push_to_new_repo(request: RepoPushRequest):
    """신규 GitHub 리포지토리를 생성하고 파일을 커밋/푸시하는 API.

    Args:
        request (RepoPushRequest): 리포지토리 이름, 파일 이름 배열.

    Returns:
        StreamingResponse: 각 단계의 진행 상황을 스트림으로 반환.
    """
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not found in .env file")

    repo_name = request.repo_name
    file_names = request.file_paths

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    project_dir = os.path.join(BASE_DIR, repo_name)

    async def event_stream():
        yield "data: Starting repository creation\n\n"

        user_resp = requests.get(f"{GITHUB_API_URL}/user", headers=headers)
        if user_resp.status_code != 200:
            raise HTTPException(status_code=user_resp.status_code, detail="Failed to get user info")
        username = user_resp.json()["login"]

        create_url = f"{GITHUB_API_URL}/user/repos"
        create_payload = {
            "name": repo_name,
            "private": False,
            "description": f"Repository created via API for {repo_name}"
        }
        create_resp = requests.post(create_url, json=create_payload, headers=headers)
        if create_resp.status_code != 201:
            error_msg = create_resp.json().get("message", "Failed to create repository")
            raise HTTPException(status_code=create_resp.status_code, detail=error_msg)

        yield f"data: Repository '{repo_name}' created successfully for user '{username}'\n\n"

        yield "data: Starting file commit process\n\n"

        if not os.path.exists(project_dir):
            yield f"data: Error: Project directory '{project_dir}' does not exist\n\n"
            yield "data: Process completed with errors\n\n"
            return

        for file_name in file_names:
            file_path = os.path.join(project_dir, file_name)
            if not os.path.exists(file_path):
                yield f"data: Error: File '{file_path}' does not exist\n\n"
                continue

            with open(file_path, "rb") as f:
                content = f.read()
            encoded_content = base64.b64encode(content).decode()

            commit_url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}/contents/{file_name}"
            commit_payload = {
                "message": f"Add {file_name} via API",
                "content": encoded_content,
                "branch": "main"
            }
            commit_resp = requests.put(commit_url, json=commit_payload, headers=headers)

            if commit_resp.status_code not in (200, 201):
                error_msg = commit_resp.json().get("message", "Failed to commit file")
                yield f"data: Error committing '{file_name}': {error_msg}\n\n"
                continue

            yield f"data: Successfully committed '{file_name}' to '{repo_name}'\n\n"

        yield "data: Process completed\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
