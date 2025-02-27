from dotenv import load_dotenv
import os

# .env 파일에서 환경 변수 로드
load_dotenv()


class Settings:
    # 데이터베이스 설정
    DB_HOST = os.getenv("DB_HOST")  # MySQL 호스트 (AWS RDS 엔드포인트)
    DB_PORT = os.getenv("DB_PORT")  # MySQL 포트
    DB_USER = os.getenv("DB_USER")  # MySQL 사용자
    DB_PASSWORD = os.getenv("DB_PASSWORD")  # MySQL 비밀번호
    DB_NAME = os.getenv("DB_NAME")  # MySQL 데이터베이스 이름

    # SQLAlchemy가 사용할 데이터베이스 연결 URL
    # 포트 번호를 포함한 연결 문자열 생성
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # GitHub 액세스 토큰
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # GitHub API 호출에 사용

    # 외부 서버 URL
    FRONTEND_URL = os.getenv("FRONTEND_URL")  # 프론트엔드 서버와 통신
    AI_LANGCHAIN_URL = os.getenv("AI_LANGCHAIN_URL")  # AI 서버와 통신


# 설정 객체 인스턴스 생성
settings = Settings()