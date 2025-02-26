import base64
import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from git import Optional
from pydantic import BaseModel
import requests

router = APIRouter()

# .env 파일에서 환경 변수 로드
load_dotenv()

# GITHUB_TOKEN과 GITHUB_USERNAME을 환경 변수로 불러오기
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

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
    source_url: Optional[str]
    repo_name: Optional[str]

# 레포지토리 생성 API
@router.post("/create-repo/")
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

BASE_DIR = "app/data/generate_projects"

# 파일 푸시 API
@router.post("/push-files/")
async def push_skeleton_files(request: RepoCreate):
    """
    로컬 디렉터리 내 모든 파일을 GitHub 레포지토리에 푸시
    """
    repo_name = request.repo_name

    # Repository 생성
    create_github_repo(repo_name)

    project_dir = os.path.join(BASE_DIR, repo_name)  # 각 프로젝트에 해당하는 디렉터리 경로

    # 해당 프로젝트 디렉터리가 존재하지 않으면 오류 발생
    if not os.path.exists(project_dir):
        raise HTTPException(status_code=400, detail=f"Project directory '{project_dir}' does not exist.")
    
    # 모든 파일 경로 가져오기
    files = get_all_files(project_dir)

    # 결과 저장할 딕셔너리
    results = {}

    for full_path, relative_path in files:
        try:
            # 파일을 GitHub 레포지토리에 푸시
            results[relative_path] = push_skeleton_file_to_repo(repo_name, full_path, relative_path)
        except HTTPException as e:
            # 오류 발생 시 그 파일은 처리되지 않음
            results[relative_path] = {"error": str(e.detail)}

    return {"results": results}