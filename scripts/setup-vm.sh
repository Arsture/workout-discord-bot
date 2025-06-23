#!/bin/bash

# GCP Compute Engine VM 초기 설정 스크립트
# 이 스크립트는 새 VM에서 한 번 실행하여 환경을 설정합니다.

set -e

echo "🚀 Workout Discord Bot VM 설정을 시작합니다..."

# 시스템 업데이트
echo "📦 시스템 패키지 업데이트 중..."
sudo apt-get update
sudo apt-get upgrade -y

# Docker 설치
echo "🐳 Docker 설치 중..."
if ! command -v docker &> /dev/null; then
    # Docker GPG 키 추가
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Docker 저장소 추가
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Docker 설치
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # 현재 사용자를 docker 그룹에 추가
    sudo usermod -aG docker $USER
    
    echo "✅ Docker 설치 완료"
else
    echo "✅ Docker가 이미 설치되어 있습니다"
fi

# Google Cloud SDK 설치 (Artifact Registry 접근용)
echo "☁️ Google Cloud SDK 설치 중..."
if ! command -v gcloud &> /dev/null; then
    # Google Cloud SDK 키 추가
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
    
    # SDK 설치
    sudo apt-get update
    sudo apt-get install -y google-cloud-cli
    
    echo "✅ Google Cloud SDK 설치 완료"
else
    echo "✅ Google Cloud SDK가 이미 설치되어 있습니다"
fi

# 필요한 유틸리티 설치
echo "🔧 유틸리티 설치 중..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    unzip \
    jq

# Docker Compose 설치 (선택사항)
echo "🐙 Docker Compose 설치 중..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose 설치 완료"
else
    echo "✅ Docker Compose가 이미 설치되어 있습니다"
fi

# 로그 디렉토리 생성
echo "📁 로그 디렉토리 생성 중..."
sudo mkdir -p /var/log/workout-bot
sudo chown $USER:$USER /var/log/workout-bot

# 방화벽 설정 (포트 8080 열기)
echo "🔥 방화벽 설정 중..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 8080/tcp
    echo "✅ 포트 8080 열림"
fi

# systemd 서비스 파일 생성 (Docker 컨테이너 관리용)
echo "⚙️ systemd 서비스 생성 중..."
sudo tee /etc/systemd/system/workout-discord-bot.service > /dev/null <<EOF
[Unit]
Description=Workout Discord Bot
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c 'docker start workout-discord-bot || echo "Container not found yet"'
ExecStop=/usr/bin/docker stop workout-discord-bot
TimeoutStartSec=0
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable workout-discord-bot.service

echo "🎉 VM 설정이 완료되었습니다!"
echo ""
echo "다음 단계:"
echo "1. 새 터미널 세션을 시작하거나 'newgrp docker' 실행"
echo "2. GitHub Actions에서 서비스 계정 키 설정"
echo "3. Artifact Registry 저장소 생성"
echo "4. GitHub에서 배포 실행"
echo ""
echo "💡 팁: 다음 명령어로 Docker가 정상 작동하는지 확인하세요:"
echo "   docker run hello-world" 