# 🚀 GCP Compute Engine 배포 가이드

이 가이드는 Workout Discord Bot을 GCP Compute Engine에 배포하고 GitHub Actions로 CI/CD를 설정하는 완전한 방법을 제공합니다.

## 📋 **사전 요구사항**

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) 설치
- GCP 프로젝트 생성 및 결제 계정 연결
- GitHub 저장소
- Supabase 프로젝트 및 테이블 생성 완료

## 🏗️ **1단계: GCP 인프라 설정**

### 1.1 로컬에서 gcloud CLI 설정

```bash
# Google Cloud에 로그인
gcloud auth login

# 기본 프로젝트 설정
gcloud config set project YOUR_PROJECT_ID
```

### 1.2 인프라 자동 생성

```bash
# 인프라 설정 스크립트 실행
./scripts/deploy-gcp.sh YOUR_PROJECT_ID
```

이 스크립트는 다음을 자동으로 생성합니다:
- ✅ Compute Engine VM (e2-micro, 프리티어 호환)
- ✅ Artifact Registry 저장소
- ✅ 방화벽 규칙 (포트 8080)
- ✅ 서비스 계정 및 권한
- ✅ 서비스 계정 키 파일

### 1.3 출력된 정보 저장

스크립트 실행 후 표시되는 정보를 안전한 곳에 저장하세요.

## 🖥️ **2단계: VM 초기 설정**

### 2.1 VM에 SSH 접속

```bash
gcloud compute ssh workout-bot-vm --zone=asia-northeast3-c
```

### 2.2 VM 환경 설정

```bash
# VM 설정 스크립트 다운로드 및 실행
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/workout-discord-bot/main/scripts/setup-vm.sh | bash

# 새 터미널 세션 시작 (Docker 그룹 적용)
newgrp docker

# Docker 설치 확인
docker run hello-world
```

## 🔐 **3단계: GitHub Secrets 설정**

GitHub 저장소 → Settings → Secrets and variables → Actions에서 다음 시크릿을 추가하세요:

### 필수 시크릿

| 이름 | 값 | 설명 |
|------|-----|------|
| `GCP_PROJECT_ID` | your-project-id | GCP 프로젝트 ID |
| `GCP_SA_KEY` | service-account-key-base64 | 서비스 계정 키 (Base64 인코딩) |
| `INSTANCE_NAME` | workout-bot-vm | VM 인스턴스 이름 |
| `INSTANCE_ZONE` | asia-northeast3-c | VM 존 |
| `DISCORD_TOKEN` | your_discord_token | Discord 봇 토큰 |
| `SUPABASE_URL` | https://xxx.supabase.co | Supabase 프로젝트 URL |
| `SUPABASE_SERVICE_ROLE_KEY` | your_supabase_key | Supabase 서비스 역할 키 |

### 선택적 시크릿

| 이름 | 기본값 | 설명 |
|------|--------|------|
| `WORKOUT_CHANNEL_NAME` | workout-debugging | 운동 채널 이름 |
| `REPORT_CHANNEL_NAME` | workout-debugging | 리포트 채널 이름 |
| `ADMIN_ROLE_NAME` | Admin | 관리자 역할 이름 |

## 🚀 **4단계: 첫 배포 실행**

### 4.1 코드 푸시

```bash
# 모든 변경사항 커밋
git add .
git commit -m "feat: add GCP deployment configuration"

# main 브랜치에 푸시 (자동 배포 트리거)
git push origin main
```

### 4.2 배포 상태 확인

1. GitHub → Actions 탭에서 워크플로우 실행 상태 확인
2. 성공적으로 완료되면 VM에서 컨테이너 상태 확인:

```bash
# VM에 SSH 접속
gcloud compute ssh workout-bot-vm --zone=asia-northeast3-c

# 컨테이너 상태 확인
docker ps
docker logs workout-discord-bot

# 헬스체크 확인
curl http://localhost:8080/
```

## 🔄 **CI/CD 워크플로우**

### 자동 배포 트리거

- **main 브랜치 푸시** → 자동 테스트 → 빌드 → 배포
- **PR 생성** → 테스트만 실행

### 배포 과정

1. **테스트**: Poetry 의존성 설치 → 린트 검사 → 테스트 실행
2. **빌드**: Docker 이미지 빌드 → Artifact Registry에 푸시
3. **배포**: VM에 SSH 접속 → 새 이미지 pull → 컨테이너 재시작

## 📊 **모니터링 및 관리**

### 로그 확인

```bash
# 실시간 로그 확인
docker logs -f workout-discord-bot

# 컨테이너 상태 확인
docker ps
docker stats workout-discord-bot
```

### 수동 재시작

```bash
# 컨테이너 재시작
docker restart workout-discord-bot

# systemd 서비스로 관리
sudo systemctl status workout-discord-bot
sudo systemctl restart workout-discord-bot
```

### VM 상태 모니터링

```bash
# VM 리소스 사용량 확인
htop

# 디스크 사용량 확인
df -h

# 메모리 사용량 확인
free -h
```

## 🛠️ **문제 해결**

### 일반적인 문제들

#### 1. 배포 실패: "Permission denied"
```bash
# VM에서 Docker 그룹 확인
groups $USER

# Docker 서비스 상태 확인
sudo systemctl status docker
```

#### 2. 컨테이너 시작 실패
```bash
# 환경변수 확인
docker inspect workout-discord-bot | grep -A 20 "Env"

# 이미지 재빌드
docker build -t workout-discord-bot .
```

#### 3. Supabase 연결 실패
```bash
# 환경변수 확인
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY

# 네트워크 연결 테스트
curl -I $SUPABASE_URL
```

### 디버깅 도구

```bash
# 컨테이너 내부 접속
docker exec -it workout-discord-bot /bin/bash

# 로그 파일 확인
tail -f /var/log/workout-bot/bot.log
```

## 💰 **비용 최적화**

### 프리티어 활용

- **e2-micro 인스턴스**: 월 744시간 무료 (24/7 가능)
- **30GB 표준 영구 디스크**: 무료
- **1GB 아웃바운드 트래픽**: 무료

### 비용 모니터링

```bash
# 현재 실행 중인 리소스 확인
gcloud compute instances list
gcloud artifacts repositories list

# 예상 비용 확인
gcloud billing budgets list
```

## 🔒 **보안 모범 사례**

### 1. 서비스 계정 키 관리
- ✅ GitHub Secrets에만 저장
- ✅ 로컬 파일은 즉시 삭제
- ✅ 정기적인 키 로테이션

### 2. 방화벽 설정
- ✅ 필요한 포트만 개방 (8080)
- ✅ 소스 IP 제한 고려

### 3. 환경변수 보안
- ✅ 민감한 정보는 GitHub Secrets 사용
- ✅ 로그에 토큰 노출 방지

## 📞 **지원 및 문의**

배포 과정에서 문제가 발생하면:

1. **GitHub Issues**에 문제 보고
2. **로그 파일** 첨부
3. **에러 메시지** 정확히 기록

---

## 🎉 **축하합니다!**

이제 전문적인 CI/CD 파이프라인이 구축되었습니다:

- ✅ **자동 배포**: main 브랜치 푸시 시 자동 배포
- ✅ **무중단 운영**: 컨테이너 기반 안정적 실행
- ✅ **확장 가능**: 필요시 VM 스펙 업그레이드 용이
- ✅ **비용 효율**: 프리티어 활용으로 무료 운영 가능

🚀 **이제 코딩에 집중하세요! 배포는 자동으로 처리됩니다.** 