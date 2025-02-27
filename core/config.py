from dotenv import load_dotenv
import os

# .env 파일에서 환경 변수 로드
load_dotenv()


class Settings:
    # SQLAlchemy가 사용할 데이터베이스 연결 URL
    # 포트 번호를 포함한 연결 문자열 생성
    DATABASE_URL = os.getenv("DATABASE_URL")

    # GitHub 액세스 토큰
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # GitHub API 호출에 사용

    # 외부 서버 URL
    FRONTEND_URL = os.getenv("FRONTEND_URL")  # 프론트엔드 서버와 통신
    AI_LANGCHAIN_URL = os.getenv("AI_LANGCHAIN_URL")  # AI 서버와 통신
    FRONTEND_PROD_URL = os.getenv("FRONTEND_PROD_URL")  # 프론트엔드 서버와 통신

# 설정 객체 인스턴스 생성
settings = Settings()
