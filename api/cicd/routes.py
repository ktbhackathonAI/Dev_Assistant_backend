from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import requests
import base64
import os
from core.config import settings
from pydantic import BaseModel
from nacl import public
import base64

router = APIRouter()

# GitHub API 기본 설정
GITHUB_API_URL = "https://api.github.com"  # GitHub API 기본 URL
GITHUB_USERNAME = settings.GITHUB_USERNAME  # GitHub 사용자 이름
GITHUB_TOKEN = settings.GITHUB_TOKEN  # GitHub 토큰
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",  # 인증 토큰
    "Accept": "application/vnd.github.v3+json"  # GitHub API 버전 3
}

def push_file_to_repo(repo_name: str, file_path: str, commit_message: str, content: str = None):
    """GitHub 레포지토리에 파일을 푸시하는 함수"""
    # GitHub API 엔드포인트
    url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo_name}/contents/{file_path}"

    # Base64로 인코딩
    encoded_content = base64.b64encode(content.encode()).decode()

    # 요청 본문
    data = {
        "message": commit_message,  # 커밋 메시지
        "content": encoded_content   # 인코딩된 파일 내용
    }

    # 파일 푸시 요청
    response = requests.put(url, json=data, headers=HEADERS)
    
    if response.status_code in [200, 201]:
        return {"message": f"File '{file_path}' uploaded successfully."}
    else:
        error_message = response.json().get("message", "Unknown error")
        raise HTTPException(status_code=response.status_code, detail=f"Failed to upload {file_path}: {error_message}")

# GitHub API에서 공개 키를 가져오는 함수
def get_public_key(owner: str, repo_name: str):
    """GitHub 레포지토리의 최신 공개 키를 가져오는 함수"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/actions/secrets/public-key"
    response = requests.get(url, headers=HEADERS)
        
    if response.status_code == 200:
        public_key_data = response.json()
        return public_key_data['key_id'], public_key_data['key']
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch public key")
    
# 공개 키로 시크릿 값을 암호화하는 함수
def encrypt_secret(secret_value: str, public_key: str):
    """주어진 공개 키로 시크릿 값을 암호화하는 함수"""
    
    # 공개 키를 바이트로 디코딩
    public_key_bytes = base64.b64decode(public_key)
    
    # 공개 키 객체 생성
    sealed_box = public.SealedBox(public.PublicKey(public_key_bytes))
    
    # 시크릿 값을 암호화
    encrypted = sealed_box.encrypt(secret_value.encode('utf-8'))
    
    # Base64로 인코딩하여 반환
    return base64.b64encode(encrypted).decode('utf-8')

def add_secret_to_repo(repo_name: str):
    """GitHub 레포지토리에 시크릿을 추가하는 함수"""
    try:
        # 필수 시크릿 값들 정의
        secrets = {
            "NCP_REGISTRY_USER": settings.NCP_REGISTRY_USER,
            "NCP_REGISTRY_PASSWORD": settings.NCP_REGISTRY_PASSWORD,
            "JARVIS_DOMAIN": settings.JARVIS_DOMAIN, 
            "NCP_DEV_SERVER_IP": settings.NCP_DEV_SERVER_IP,
            "NCP_DEV_SSH_PASSWORD": settings.NCP_DEV_SSH_PASSWORD,
            "ENV_GITHUB_TOKEN": settings.GITHUB_TOKEN,
            "ENV_GITHUB_USERNAME": settings.GITHUB_USERNAME
        }
        
        # 각 시크릿에 대해 처리
        for secret_name, secret_value in secrets.items():
            try:
                # 최신 공개 키 가져오기
                key_id, public_key = get_public_key(settings.GITHUB_USERNAME, repo_name)
                
                # 시크릿 값 암호화
                encrypted_value = encrypt_secret(secret_value, public_key)
                
                # 시크릿을 추가하는 API 엔드포인트
                url = f"{GITHUB_API_URL}/repos/{settings.GITHUB_USERNAME}/{repo_name}/actions/secrets/{secret_name}"
                
                # 시크릿 추가 요청 본문
                payload = {
                    "encrypted_value": encrypted_value,
                    "key_id": key_id
                }
                
                # GitHub API 요청 보내기
                response = requests.put(url, json=payload, headers=HEADERS)
                
                if response.status_code not in [201, 204]:
                    raise HTTPException(status_code=response.status_code, detail=f"Failed to add secret {secret_name}: {response.text}")
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to add secret {secret_name}: {str(e)}")
        
        return {"message": f"Successfully added all secrets to {repo_name}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process secrets: {str(e)}")

class PublishRepoRequest(BaseModel):
    repo_name: str

@router.post("/publish-repo")
async def publish_repo(request: PublishRepoRequest):
    """GitHub 레포지토리를 배포하는 엔드포인트"""
    try:
        # 레포지토리 존재 여부 확인
        repo_url = f"https://github.com/{settings.GITHUB_USERNAME}/{request.repo_name}"
        response = requests.get(repo_url, headers=HEADERS)
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # 도커 파일 푸시
        with open(os.path.join(os.getcwd(), "api/cicd/Dockerfile"), 'r', encoding='utf-8') as file:
            dockerfilecontent = file.read()

        push_file_to_repo(
            repo_name=request.repo_name,
            file_path="Dockerfile",
            content=dockerfilecontent,
            commit_message=f"Add Dockerfile from local"
        )

        add_secret_to_repo(request.repo_name)
        
        with open(os.path.join(os.getcwd(), "api/cicd/main.yml"), 'r', encoding='utf-8') as file:
            cicdworkflowcontent = file.read()

        push_file_to_repo(
            repo_name=request.repo_name,
            file_path=".github/workflows/main.yml",
            content=cicdworkflowcontent,
            commit_message=f"Add Docker CI/CD Workflow from local"
        )

        return {
            "message": f"Successfully published {request.repo_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish repository: {str(e)}")
