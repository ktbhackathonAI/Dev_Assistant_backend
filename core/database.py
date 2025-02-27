from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# SQLAlchemy 엔진 생성: MySQL에 연결
engine = create_engine(settings.DATABASE_URL)

# 세션 팩토리 생성: 데이터베이스 세션을 관리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy 모델의 기본 클래스: 테이블 정의에 사용
Base = declarative_base()

# 데이터베이스 세션을 의존성 주입으로 제공하는 함수
def get_db():
    db = SessionLocal()  # 새로운 세션 생성
    try:
        yield db         # FastAPI에서 사용하도록 세션 제공
    finally:
        db.close()       # 요청이 끝나면 세션 닫기
