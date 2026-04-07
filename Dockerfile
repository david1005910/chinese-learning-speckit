# 1. 파이썬 3.10 슬림 버전 사용 (용량이 가볍습니다)
FROM python:3.10-slim

# 2. 컨테이너 내부의 작업 디렉토리를 /app으로 설정
WORKDIR /app

# 3. 필수 도구 설치 (Playwright 브라우저 설치 시 필요한 시스템 라이브러리들)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. 라이브러리 설치 (소스 코드 복사 전에 먼저 해서 빌드 속도를 높입니다)
# 만약 requirements.txt 파일이 있다면 아래 주석을 해제하세요.
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir streamlit playwright

# 5. ★핵심★ Playwright 브라우저 및 의존성 설치
# 'python -m'을 붙여서 실행하는 것이 가장 안전하게 패키지를 찾는 방법입니다.
RUN python -m playwright install --with-deps chromium

# 6. 현재 내 모든 소스코드(app.py 등)를 컨테이너의 /app 폴더로 복사
# (점 하나 찍고 한 칸 띄우고 점 하나 더 찍는 것이 포인트!)
COPY . .

# 7. 스트림릿 기본 포트 8501 열기
EXPOSE 8501

# 8. 앱 실행 (8501 포트로 외부 접속 허용 설정 포함)
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
