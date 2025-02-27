from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # CORS 미들웨어 임포트
from core.database import Base, engine
from core.config import settings  # 환경 변수 로드
from api.chat.routes import router as chat_router
from api.ai.routes import router as ai_router
from api.github.routes import router as github_router

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI()

# CORS 설정
# 허용할 출처 목록: 프론트엔드와 AI 서버 URL
origins = [
    settings.FRONTEND_URL,      # 예: "http://frontend:3000"
    settings.AI_LANGCHAIN_URL,  # 예: "http://ai-server:8001"
    settings.FRONTEND_PROD_URL,  # 예: "http://frontend:3000"
]

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # 허용된 출처 목록
    allow_credentials=True,         # 인증 정보(쿠키, Authorization 헤더 등) 허용
    allow_methods=["*"],            # 모든 HTTP 메서드 허용 (GET, POST, PUT 등)
    allow_headers=["*"],            # 모든 헤더 허용
)

# 데이터베이스 테이블 생성: 서버 시작 시 실행
Base.metadata.create_all(bind=engine)

# API 라우터 등록: 각 기능별 엔드포인트를 모듈화
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(ai_router, prefix="/ai", tags=["ai"])
app.include_router(github_router, prefix="/github", tags=["github"])

# 루트 엔드포인트
@app.get("/")
def read_root():
    return {"message": "Welcome to the JAVIS"}

#
# # 레포지토리 생성 함수
# def create_github_repo(repo_name: str):
#     url = "https://api.github.com/user/repos"
#     headers = {
#         "Authorization": f"token {GITHUB_TOKEN}",
#         "Accept": "application/vnd.github.v3+json"
#     }
#     data = {
#         "name": repo_name,
#         "private": True,  # 개인 레포지토리로 설정
#         "description": f"Repository for {repo_name}",
#     }
#
#     response = requests.post(url, json=data, headers=headers)
#
#     if response.status_code == 201:
#         repo_url = response.json()["ssh_url"]
#         return {"message": f"Repository '{repo_name}' created successfully!", "repo_url": repo_url}
#     else:
#         raise HTTPException(status_code=response.status_code, detail="Failed to create repository")
#
# # 레포지토리 생성 API
# @app.post("/create-repo/")
# async def create_repo(repo_name: str):
#     result = create_github_repo(repo_name)
#     return result
