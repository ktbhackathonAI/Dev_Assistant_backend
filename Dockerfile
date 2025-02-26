# 1. Python 3.10 이미지 사용
FROM python:3.10

# 2. 기본 작업 디렉토리 설정 제거 (현재 디렉토리 사용)
# WORKDIR /app  # ❌ 제거

# 3. 필수 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 애플리케이션 코드 복사
COPY . .

# 5. FastAPI 실행 (현재 디렉토리 기준)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
