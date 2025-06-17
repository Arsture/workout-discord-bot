# Python 3.13 slim 이미지 사용 (보안 및 크기 최적화)
FROM python:3.13-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install poetry

# Poetry 설정 (가상환경을 컨테이너 내에서 생성하지 않음)
RUN poetry config virtualenvs.create false

# 의존성 파일 복사
COPY pyproject.toml poetry.lock ./

# 프로덕션 의존성만 설치
RUN poetry install --only=main --no-dev

# 애플리케이션 코드 복사
COPY . .

# 사용자 생성 (보안 강화)
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 환경변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# 포트 노출
EXPOSE 8080

# 애플리케이션 실행
CMD ["python", "main.py"] 