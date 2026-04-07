# 1. 파이썬 베이스 이미지
FROM python:3.10-slim

# 2. 시스템 패키지 설치 (Playwright 및 TTS 라이브러리용 의존성)
RUN apt-get update && apt-get install -y \
    curl \
    libnss3 \
    libnspr4 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. 라이브러리 설치 (소스 코드 복사 전에 실행하여 빌드 속도 최적화)
# requirements.txt가 있다면 COPY requirements.txt . 후 설치하세요.
RUN pip install --no-cache-dir streamlit playwright edge-tts gTTS matplotlib pandas

# 5. Playwright 브라우저 설치
RUN python -m playwright install chromium

# 6. ★핵심★ 현재 폴더의 모든 내용(src, ai, ui 등)을 컨테이너의 /app으로 복사
COPY . .

# 7. 환경 변수 설정 (파이썬이 루트 폴더를 인식하게 함)
ENV PYTHONPATH=/app

# 8. 포트 설정
EXPOSE 8501

# 9. 실행 명령 (ui/app.py 경로를 정확히 지정)
# ★ 수정 포인트: 파일 경로에 src/를 추가합니다.
ENTRYPOINT ["streamlit", "run", "src/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
