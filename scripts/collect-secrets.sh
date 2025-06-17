#!/bin/bash

# GitHub Secrets 수집 도우미 스크립트
# 이 스크립트는 필요한 환경변수들을 수집하고 GitHub Secrets 형태로 출력합니다.

set -e

echo "🔐 GitHub Secrets 수집 도우미"
echo "================================"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 환경변수 수집 함수
collect_secrets() {
    echo -e "${BLUE}📋 필요한 환경변수들을 수집합니다...${NC}"
    echo ""
    
    # GCP 관련
    echo -e "${YELLOW}🏗️ GCP 관련 정보${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    read -p "GCP Project ID를 입력하세요: " GCP_PROJECT_ID
    
    # 서비스 계정 키 파일 확인
    KEY_FILE="github-actions-key.json"
    if [ -f "$KEY_FILE" ]; then
        echo -e "${GREEN}✅ 서비스 계정 키 파일을 찾았습니다: $KEY_FILE${NC}"
        GCP_SA_KEY=$(cat $KEY_FILE | base64 -w 0)
    else
        echo -e "${RED}❌ 서비스 계정 키 파일을 찾을 수 없습니다.${NC}"
        echo "먼저 ./scripts/deploy-gcp.sh 스크립트를 실행하세요."
        exit 1
    fi
    
    INSTANCE_NAME="workout-bot-vm"
    INSTANCE_ZONE="asia-northeast3-c"
    
    echo ""
    
    # Discord 관련
    echo -e "${YELLOW}🤖 Discord 관련 정보${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Discord Developer Portal (https://discord.com/developers/applications)에서"
    echo "봇 토큰을 복사해서 입력하세요."
    echo ""
    read -p "Discord Bot Token을 입력하세요: " DISCORD_TOKEN
    echo ""
    
    # Supabase 관련
    echo -e "${YELLOW}🗄️ Supabase 관련 정보${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Supabase Dashboard → Settings → API에서 정보를 복사하세요."
    echo ""
    read -p "Supabase URL을 입력하세요 (예: https://xxx.supabase.co): " SUPABASE_URL
    echo ""
    echo "⚠️  'service_role' 키를 입력하세요 ('anon' 키가 아닙니다!)"
    read -p "Supabase Service Role Key를 입력하세요: " SUPABASE_SERVICE_ROLE_KEY
    echo ""
    
    # 선택적 환경변수
    echo -e "${YELLOW}⚙️ 선택적 설정 (Enter로 기본값 사용)${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    read -p "운동 채널 이름 (기본: workout): " WORKOUT_CHANNEL_NAME
    WORKOUT_CHANNEL_NAME=${WORKOUT_CHANNEL_NAME:-workout}
    
    read -p "리포트 채널 이름 (기본: workout): " REPORT_CHANNEL_NAME
    REPORT_CHANNEL_NAME=${REPORT_CHANNEL_NAME:-workout}
    
    read -p "관리자 역할 이름 (기본: Admin): " ADMIN_ROLE_NAME
    ADMIN_ROLE_NAME=${ADMIN_ROLE_NAME:-Admin}
    
    echo ""
}

# GitHub Secrets 출력 함수
output_secrets() {
    echo -e "${GREEN}🎉 GitHub Secrets 설정 정보${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "다음 정보를 GitHub Repository → Settings → Secrets and variables → Actions에서"
    echo "'New repository secret'으로 각각 추가하세요:"
    echo ""
    
    echo -e "${BLUE}필수 시크릿:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Name: GCP_PROJECT_ID"
    echo "Value: $GCP_PROJECT_ID"
    echo ""
    echo "Name: GCP_SA_KEY"
    echo "Value: $GCP_SA_KEY"
    echo ""
    echo "Name: INSTANCE_NAME"
    echo "Value: $INSTANCE_NAME"
    echo ""
    echo "Name: INSTANCE_ZONE"
    echo "Value: $INSTANCE_ZONE"
    echo ""
    echo "Name: DISCORD_TOKEN"
    echo "Value: $DISCORD_TOKEN"
    echo ""
    echo "Name: SUPABASE_URL"
    echo "Value: $SUPABASE_URL"
    echo ""
    echo "Name: SUPABASE_SERVICE_ROLE_KEY"
    echo "Value: $SUPABASE_SERVICE_ROLE_KEY"
    echo ""
    
    echo -e "${BLUE}선택적 시크릿 (기본값과 다른 경우에만 추가):${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if [ "$WORKOUT_CHANNEL_NAME" != "workout" ]; then
        echo "Name: WORKOUT_CHANNEL_NAME"
        echo "Value: $WORKOUT_CHANNEL_NAME"
        echo ""
    fi
    
    if [ "$REPORT_CHANNEL_NAME" != "workout" ]; then
        echo "Name: REPORT_CHANNEL_NAME"
        echo "Value: $REPORT_CHANNEL_NAME"
        echo ""
    fi
    
    if [ "$ADMIN_ROLE_NAME" != "Admin" ]; then
        echo "Name: ADMIN_ROLE_NAME"
        echo "Value: $ADMIN_ROLE_NAME"
        echo ""
    fi
}

# 파일로 저장 함수
save_to_file() {
    local filename="github-secrets-$(date +%Y%m%d-%H%M%S).txt"
    
    echo "GitHub Secrets 설정 정보" > $filename
    echo "생성일시: $(date)" >> $filename
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> $filename
    echo "" >> $filename
    echo "필수 시크릿:" >> $filename
    echo "GCP_PROJECT_ID: $GCP_PROJECT_ID" >> $filename
    echo "GCP_SA_KEY: $GCP_SA_KEY" >> $filename
    echo "INSTANCE_NAME: $INSTANCE_NAME" >> $filename
    echo "INSTANCE_ZONE: $INSTANCE_ZONE" >> $filename
    echo "DISCORD_TOKEN: $DISCORD_TOKEN" >> $filename
    echo "SUPABASE_URL: $SUPABASE_URL" >> $filename
    echo "SUPABASE_SERVICE_ROLE_KEY: $SUPABASE_SERVICE_ROLE_KEY" >> $filename
    echo "" >> $filename
    echo "선택적 시크릿:" >> $filename
    echo "WORKOUT_CHANNEL_NAME: $WORKOUT_CHANNEL_NAME" >> $filename
    echo "REPORT_CHANNEL_NAME: $REPORT_CHANNEL_NAME" >> $filename
    echo "ADMIN_ROLE_NAME: $ADMIN_ROLE_NAME" >> $filename
    
    echo -e "${GREEN}✅ 정보가 $filename 파일에 저장되었습니다.${NC}"
    echo -e "${YELLOW}⚠️  이 파일에는 민감한 정보가 포함되어 있습니다.${NC}"
    echo -e "${YELLOW}   GitHub Secrets 설정 후 안전하게 삭제하세요.${NC}"
}

# 메인 실행
main() {
    collect_secrets
    output_secrets
    
    echo ""
    read -p "이 정보를 파일로 저장하시겠습니까? (y/N): " save_choice
    if [[ $save_choice =~ ^[Yy]$ ]]; then
        save_to_file
    fi
    
    echo ""
    echo -e "${GREEN}🚀 다음 단계:${NC}"
    echo "1. 위의 정보를 GitHub Secrets에 추가"
    echo "2. 코드를 main 브랜치에 푸시하여 배포 테스트"
    echo "3. GitHub Actions에서 배포 상태 확인"
    echo ""
    echo -e "${BLUE}💡 도움말:${NC}"
    echo "- Discord 설정: docs/discord-setup.md"
    echo "- Supabase 설정: docs/supabase-setup.md"
    echo "- GitHub Secrets 설정: docs/github-secrets-setup.md"
}

# 스크립트 실행
main 