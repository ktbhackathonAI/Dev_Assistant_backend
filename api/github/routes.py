from fastapi import APIRouter, HTTPException, Depends  # FastAPI 관련 모듈 임포트
from sqlalchemy.orm import Session  # SQLAlchemy 세션 관리
from core.database import get_db  # 데이터베이스 연결 함수
from core.config import settings  # 환경 변수 설정 모듈
import aiohttp  # 비동기 HTTP 요청 처리 라이브러리
import base64  # 파일 내용을 Base64로 인코딩/디코딩

# API 라우터 객체 생성: '/github' 접두어 하위에 엔드포인트 정의
router = APIRouter()

# GitHub API 기본 설정 상수
GITHUB_API_URL = "https://api.github.com"  # GitHub REST API 기본 엔드포인트
HEADERS = {
    "Authorization": f"Bearer {settings.GITHUB_TOKEN}",  # 인증 토큰을 헤더에 포함
    "Accept": "application/vnd.github.v3+json"  # GitHub API 버전 3을 JSON 형식으로 요청
}


@router.post("/create-repo")  # POST 요청을 '/github/create-repo' 경로로 처리
async def create_repo(repo_name: str, db: Session = Depends(get_db)):
    """새로운 GitHub 리포지토리를 생성하는 엔드포인트.

    Args:
        repo_name (str): 생성할 리포지토리 이름.
        db (Session): 데이터베이스 세션 (현재 미사용, 확장 가능성으로 유지).

    Returns:
        dict: 생성된 리포지토리의 URL을 포함한 응답.

    Raises:
        HTTPException: GitHub API 호출 실패 시 오류 반환.
    """
    # 사용자 계정에 리포지토리를 생성하기 위한 GitHub API 엔드포인트
    url = f"{GITHUB_API_URL}/user/repos"

    # 요청 본문: 리포지토리 이름과 공개/비공개 설정 포함
    payload = {
        "name": repo_name,  # 리포지토리 이름
        "private": False  # 공개 리포지토리로 설정 (True로 변경 시 비공개)
    }

    # 비동기 HTTP 클라이언트 세션 시작
    async with aiohttp.ClientSession() as session:
        # GitHub API에 POST 요청 보내기
        async with session.post(url, json=payload, headers=HEADERS) as resp:
            if resp.status != 201:  # 201 Created가 아니면 실패로 간주
                error_detail = await resp.text()  # 오류 메시지 가져오기
                raise HTTPException(
                    status_code=resp.status,
                    detail=f"Failed to create repo: {error_detail}"  # 클라이언트에 오류 전달
                )
            repo_data = await resp.json()  # 성공 시 응답 JSON 파싱

    # 생성된 리포지토리의 웹 URL 반환
    return {"repo_url": repo_data["html_url"]}


@router.post("/repos/{repo_name}/commit")  # POST 요청을 '/github/repos/{repo_name}/commit' 경로로 처리
async def commit_to_repo(repo_name: str, file_path: str, commit_message: str):
    """지정된 리포지토리에 파일을 커밋하는 엔드포인트.

    Args:
        repo_name (str): 대상 리포지토리 이름.
        file_path (str): 커밋할 로컬 파일 경로 (리포지토리 내 경로로 사용).
        commit_message (str): 커밋 메시지.

    Returns:
        dict: 커밋 성공 메시지와 커밋 URL 포함.

    Raises:
        HTTPException: 사용자 정보 가져오기 실패 또는 커밋 실패 시 오류 반환.
    """
    # 비동기 HTTP 클라이언트 세션 시작
    async with aiohttp.ClientSession() as session:
        # 현재 인증된 사용자의 GitHub 사용자 이름 가져오기
        async with session.get(f"{GITHUB_API_URL}/user", headers=HEADERS) as resp:
            if resp.status != 200:  # 200 OK가 아니면 실패
                raise HTTPException(status_code=resp.status, detail="Failed to get user info")
            user_data = await resp.json()  # 응답 JSON 파싱
            username = user_data["login"]  # 사용자 이름 추출

        # 커밋할 파일 읽기 및 Base64 인코딩
        with open(file_path, "r") as f:
            content = f.read()  # 파일 내용을 문자열로 읽기
        encoded_content = base64.b64encode(content.encode()).decode()  # UTF-8로 인코딩 후 Base64 변환

        # 파일을 리포지토리에 업로드하기 위한 GitHub API 엔드포인트
        url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}/contents/{file_path}"

        # 요청 본문: 커밋 메시지와 Base64 인코딩된 파일 내용 포함
        payload = {
            "message": commit_message,  # 커밋 메시지
            "content": encoded_content  # 인코딩된 파일 내용
        }

        # GitHub API에 PUT 요청으로 파일 커밋
        async with session.put(url, json=payload, headers=HEADERS) as resp:
            if resp.status not in (201, 200):  # 201 Created 또는 200 OK가 아니면 실패
                error_detail = await resp.text()  # 오류 메시지 가져오기
                raise HTTPException(
                    status_code=resp.status,
                    detail=f"Failed to commit: {error_detail}"  # 클라이언트에 오류 전달
                )
            commit_data = await resp.json()  # 성공 시 응답 JSON 파싱

    # 커밋 성공 메시지와 커밋 URL 반환
    return {
        "message": f"Committed {file_path} to {repo_name}",
        "commit_url": commit_data["commit"]["html_url"]
    }