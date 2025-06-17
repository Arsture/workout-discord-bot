#!/bin/bash

# GCP 인프라 설정 스크립트
# 이 스크립트는 로컬에서 실행하여 GCP 리소스를 생성합니다.

set -e

# 설정 변수
PROJECT_ID="${1:-your-project-id}"
REGION="asia-northeast3"  # 서울 리전
ZONE="asia-northeast3-c"
INSTANCE_NAME="workout-bot-vm"
MACHINE_TYPE="e2-micro"  # 프리티어 호환
REPOSITORY_NAME="workout-discord-bot"

echo "🚀 GCP 인프라 설정을 시작합니다..."
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Zone: $ZONE"

# gcloud CLI 로그인 확인
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ gcloud CLI에 로그인이 필요합니다."
    echo "다음 명령어를 실행하세요: gcloud auth login"
    exit 1
fi

# 프로젝트 설정
echo "📋 프로젝트 설정 중..."
gcloud config set project $PROJECT_ID

# 필요한 API 활성화
echo "🔌 필요한 API 활성화 중..."
gcloud services enable compute.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Artifact Registry 저장소 생성
echo "📦 Artifact Registry 저장소 생성 중..."
if ! gcloud artifacts repositories describe $REPOSITORY_NAME --location=$REGION &>/dev/null; then
    gcloud artifacts repositories create $REPOSITORY_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="Workout Discord Bot container images"
    echo "✅ Artifact Registry 저장소 생성 완료"
else
    echo "✅ Artifact Registry 저장소가 이미 존재합니다"
fi

# 방화벽 규칙 생성 (헬스체크용 포트 8080)
echo "🔥 방화벽 규칙 생성 중..."
if ! gcloud compute firewall-rules describe allow-workout-bot-port &>/dev/null; then
    gcloud compute firewall-rules create allow-workout-bot-port \
        --allow tcp:8080 \
        --source-ranges 0.0.0.0/0 \
        --description "Allow port 8080 for workout bot health checks"
    echo "✅ 방화벽 규칙 생성 완료"
else
    echo "✅ 방화벽 규칙이 이미 존재합니다"
fi

# Compute Engine VM 생성
echo "🖥️ Compute Engine VM 생성 중..."
if ! gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE &>/dev/null; then
    gcloud compute instances create $INSTANCE_NAME \
        --zone=$ZONE \
        --machine-type=$MACHINE_TYPE \
        --network-interface=network-tier=PREMIUM,subnet=default \
        --maintenance-policy=MIGRATE \
        --scopes=https://www.googleapis.com/auth/cloud-platform \
        --tags=workout-bot \
        --image-family=ubuntu-2204-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=20GB \
        --boot-disk-type=pd-standard \
        --boot-disk-device-name=$INSTANCE_NAME \
        --shielded-vtpm \
        --shielded-integrity-monitoring \
        --labels=environment=production,application=workout-discord-bot
    
    echo "✅ VM 생성 완료"
    
    # VM이 시작될 때까지 대기
    echo "⏳ VM 시작 대기 중..."
    while true; do
        STATUS=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format="value(status)")
        if [ "$STATUS" = "RUNNING" ]; then
            echo "✅ VM이 실행 중입니다"
            break
        fi
        echo "VM 상태: $STATUS (대기 중...)"
        sleep 5
    done
    
else
    echo "✅ VM이 이미 존재합니다"
fi

# 서비스 계정 생성 (GitHub Actions용)
echo "🔑 서비스 계정 생성 중..."
SERVICE_ACCOUNT_NAME="github-actions-sa"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &>/dev/null; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="GitHub Actions Service Account" \
        --description="Service account for GitHub Actions CI/CD"
    echo "✅ 서비스 계정 생성 완료"
else
    echo "✅ 서비스 계정이 이미 존재합니다"
fi

# 서비스 계정 권한 부여
echo "👤 서비스 계정 권한 설정 중..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/compute.instanceAdmin.v1"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/compute.osLogin"

# 서비스 계정 키 생성
echo "🗝️ 서비스 계정 키 생성 중..."
KEY_FILE="github-actions-key.json"
if [ ! -f "$KEY_FILE" ]; then
    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=$SERVICE_ACCOUNT_EMAIL
    echo "✅ 서비스 계정 키 생성 완료: $KEY_FILE"
else
    echo "✅ 서비스 계정 키가 이미 존재합니다: $KEY_FILE"
fi

# VM 외부 IP 주소 가져오기
EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "🎉 GCP 인프라 설정이 완료되었습니다!"
echo ""
echo "📋 다음 정보를 GitHub Secrets에 추가하세요:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "GCP_PROJECT_ID: $PROJECT_ID"
echo "GCP_SA_KEY: $(cat $KEY_FILE | base64 -w 0)"
echo "INSTANCE_NAME: $INSTANCE_NAME"
echo "INSTANCE_ZONE: $ZONE"
echo "DISCORD_TOKEN: your_discord_token"
echo "SUPABASE_URL: your_supabase_url"
echo "SUPABASE_SERVICE_ROLE_KEY: your_supabase_key"
echo "WORKOUT_CHANNEL_NAME: workout-debugging"
echo "REPORT_CHANNEL_NAME: workout-debugging"
echo "ADMIN_ROLE_NAME: Admin"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🖥️ VM 정보:"
echo "Instance Name: $INSTANCE_NAME"
echo "External IP: $EXTERNAL_IP"
echo "Zone: $ZONE"
echo ""
echo "📦 Artifact Registry:"
echo "Repository: $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY_NAME"
echo ""
echo "🔧 다음 단계:"
echo "1. VM에 SSH 접속: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo "2. VM 설정 스크립트 실행: wget -O - https://raw.githubusercontent.com/your-repo/main/scripts/setup-vm.sh | bash"
echo "3. GitHub Secrets 설정"
echo "4. 코드를 main 브랜치에 푸시하여 배포 테스트"
echo ""
echo "⚠️ 보안 주의사항:"
echo "- $KEY_FILE 파일을 안전한 곳에 보관하고 GitHub에 커밋하지 마세요"
echo "- GitHub Secrets에 추가한 후 로컬 파일을 삭제하는 것을 고려하세요" 