# 1. 베이스 이미지
FROM python:3.10-slim

# 2. 시스템 의존성 설치 (TTS 및 Playwright용)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. 라이브러리 설치
# (ui/app.py에서 사용하는 edge-tts, streamlit, matplotlib, sqlite3 등 포함 확인)
RUN pip install --no-cache-dir streamlit playwright edge-tts gTTS matplotlib pandas

# 4. Playwright 브라우저 설치
RUN python -m playwright install --with-deps chromium

# 5. ★핵심★ 현재 폴더(src가 포함된 폴더) 전체를 /app으로 복사
COPY . .

# 6. 포트 설정
EXPOSE 8501

# 7. 실행 명령 (app.py의 정확한 경로인 ui/app.py를 지정)
# --server.address=0.0.0.0 설정은 외부(Tailscale) 접속을 위해 필수입니다.
ENTRYPOINT ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
