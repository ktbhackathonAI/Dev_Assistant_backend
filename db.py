from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os


# .env 파일에서 환경 변수 로드
load_dotenv()

DATABASE_URL = "mysql+pymysql://jhy:wjdghdus1!@gb-prod.c9wgecae8edg.ap-northeast-2.rds.amazonaws.com:3306/ktbdb"
# SQLAlchemy 엔진 생성
engine = create_engine(DATABASE_URL)

# DB 연결을 시도해볼 수 있습니다.
try:
    with engine.connect() as connection:
        print("MySQL 연결 성공")
except Exception as e:
    print(f"연결 실패: {e}")

# SQLAlchemy 모델 기본 클래스
Base = declarative_base()

# 세션 생성자 정의 (SessionLocal)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# DB 세션을 FastAPI의 Dependency로 제공
def get_db():
    db = SessionLocal()  # 세션 생성
    try:
        yield db  # 세션을 FastAPI 의존성 주입 시스템에 제공
    finally:
        db.close()  # 사용 후 세션 닫기
