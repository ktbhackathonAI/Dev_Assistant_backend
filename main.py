from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# ✅ 데이터베이스 설정 (기본: SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")  # MySQL 또는 PostgreSQL로 변경 가능

# ✅ SQLAlchemy 엔진 및 세션 생성
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ SQLAlchemy 모델 기본 클래스
Base = declarative_base()

# ✅ FastAPI 앱 생성
app = FastAPI()

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
    return {"message": "Welcome to FastAPI Post CRUD API"}