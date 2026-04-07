# 1. 베이스 이미지
FROM python:3.10-slim

# 2. 필수 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 생성 및 설정
WORKDIR /app

# 4. 라이브러리 설치 (캐시 활용을 위해 소스 복사 전에 수행)
RUN pip install --no-cache-dir streamlit playwright
RUN python -m playwright install --with-deps chromium

# 5. ★중요★ 현재 폴더의 모든 파일(app.py 포함)을 컨테이너의 /app으로 복사
COPY . .

# 6. 실행 시 경로를 명시적으로 지정
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "/app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
