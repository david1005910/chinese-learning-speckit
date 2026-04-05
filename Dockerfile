# 1. 베이스 이미지 선택 (파이썬 3.10 slim 버전으로 용량 최적화)
FROM python:3.10-slim

# 2. 시스템 의존성 설치 (음성 처리 및 브라우저 테스트용 필수 패키지)
# SpeechRecognition 및 Playwright 실행에 필요한 라이브러리들입니다.
# 6번 라인부터 수정
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. 의존성 파일 복사 및 설치
# (캐시 효율을 위해 소스 코드보다 requirements.txt를 먼저 복사합니다)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Playwright 브라우저 설치 (테스트 도구 사용 시 필요)
RUN playwright install --with-deps chromium

# 6. 전체 소스 코드 복사
COPY . .

# 7. Streamlit 기본 포트 개방
EXPOSE 8501

# 8. 컨테이너 실행 시 Streamlit 서버 실행
# --server.address=0.0.0.0 설정이 있어야 외부(CasaOS)에서 접속 가능합니다.
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
