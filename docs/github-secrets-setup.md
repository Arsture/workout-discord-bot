# 🔐 GitHub Secrets 설정 완전 가이드

## 환경변수 수집 및 GitHub Secrets 추가 방법

### 📋 **1단계: 필요한 모든 환경변수 수집**

#### 🏗️ **GCP 관련 (deploy-gcp.sh 실행 후 얻음)**

```bash
# 인프라 설정 스크립트 실행
./scripts/deploy-gcp.sh YOUR_PROJECT_ID
```

실행 후 출력되는 정보:

| GitHub Secret 이름 | 값 예시 | 설명 |
|-------------------|---------|------|
| `GCP_PROJECT_ID` | `my-workout-bot-project` | GCP 프로젝트 ID |
| `GCP_SA_KEY` | `eyJhbGciOiJSUzI1NiIs...` | 서비스 계정 키 (Base64 인코딩됨) |
| `INSTANCE_NAME` | `workout-bot-vm` | VM 인스턴스 이름 |
| `INSTANCE_ZONE` | `asia-northeast3-c` | VM 존 |

#### 🤖 **Discord 관련**

| GitHub Secret 이름 | 값 예시 | 얻는 방법 |
|-------------------|---------|----------|
| `DISCORD_TOKEN` | `MTIzNDU2Nzg5MDEyMzQ1Njc4OTA...` | [Discord 설정 가이드](./discord-setup.md) 참조 |

#### 🗄️ **Supabase 관련**

| GitHub Secret 이름 | 값 예시 | 얻는 방법 |
|-------------------|---------|----------|
| `SUPABASE_URL` | `https://abcdefgh.supabase.co` | [Supabase 설정 가이드](./supabase-setup.md) 참조 |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` | [Supabase 설정 가이드](./supabase-setup.md) 참조 |

#### ⚙️ **선택적 환경변수 (기본값 있음)**

| GitHub Secret 이름 | 기본값 | 설명 |
|-------------------|--------|------|
| `WORKOUT_CHANNEL_NAME` | `workout` | 운동 기록 채널 이름 |
| `REPORT_CHANNEL_NAME` | `workout` | 리포트 전송 채널 이름 |
| `ADMIN_ROLE_NAME` | `Admin` | 관리자 역할 이름 |

### 🔧 **2단계: GitHub Secrets 추가하기**

#### 2.1 GitHub 저장소 접속
1. GitHub에서 프로젝트 저장소 접속
2. **Settings** 탭 클릭
3. 왼쪽 메뉴에서 **Secrets and variables** → **Actions** 클릭

#### 2.2 Secrets 추가
각 환경변수에 대해 다음 단계 반복:

1. **"New repository secret"** 버튼 클릭
2. **Name** 필드에 시크릿 이름 입력 (예: `DISCORD_TOKEN`)
3. **Secret** 필드에 값 입력
4. **"Add secret"** 버튼 클릭

### 📝 **3단계: 체크리스트로 확인**

모든 시크릿이 올바르게 추가되었는지 확인:

#### ✅ **필수 시크릿 (7개)**
- [ ] `GCP_PROJECT_ID`
- [ ] `GCP_SA_KEY`
- [ ] `INSTANCE_NAME`
- [ ] `INSTANCE_ZONE`
- [ ] `DISCORD_TOKEN`
- [ ] `SUPABASE_URL`
- [ ] `SUPABASE_SERVICE_ROLE_KEY`

#### ✅ **선택적 시크릿 (필요시 추가)**
- [ ] `WORKOUT_CHANNEL_NAME` (기본: `workout`)
- [ ] `REPORT_CHANNEL_NAME` (기본: `workout`)
- [ ] `ADMIN_ROLE_NAME` (기본: `Admin`)

### 🚀 **4단계: 배포 테스트**

모든 시크릿 추가 후:

```bash
# 코드 커밋 및 푸시
git add .
git commit -m "feat: configure GitHub secrets for deployment"
git push origin main
```

GitHub Actions가 자동으로 실행되어 배포가 진행됩니다.

### 🔍 **5단계: 배포 상태 확인**

1. **GitHub Actions 확인**:
   - GitHub → Actions 탭에서 워크플로우 상태 확인
   - 빨간색(실패) 시 로그 확인

2. **VM에서 확인**:
   ```bash
   # VM에 SSH 접속
   gcloud compute ssh workout-bot-vm --zone=asia-northeast3-c
   
   # 컨테이너 상태 확인
   docker ps
   docker logs workout-discord-bot
   
   # 헬스체크 확인
   curl http://localhost:8080/
   ```

### ⚠️ **보안 주의사항**

#### 절대 하지 말 것:
- ❌ 시크릿을 코드에 하드코딩
- ❌ 시크릿을 GitHub 커밋에 포함
- ❌ 시크릿을 로그에 출력
- ❌ 시크릿을 다른 사람과 공유

#### 반드시 할 것:
- ✅ GitHub Secrets에만 저장
- ✅ 정기적인 키 로테이션
- ✅ 최소 권한 원칙 적용
- ✅ 사용하지 않는 키 즉시 삭제

### 🛠️ **문제 해결**

#### 자주 발생하는 오류:

1. **"Invalid token" 오류**:
   - Discord 토큰이 잘못되었거나 만료됨
   - Discord Developer Portal에서 토큰 재생성

2. **"Authentication failed" 오류**:
   - GCP 서비스 계정 키가 잘못됨
   - 스크립트를 다시 실행하여 새 키 생성

3. **"Table doesn't exist" 오류**:
   - Supabase 테이블이 생성되지 않음
   - Supabase SQL Editor에서 테이블 생성 스크립트 실행

4. **"Permission denied" 오류**:
   - VM 권한 문제
   - `scripts/setup-vm.sh` 스크립트 재실행

### 📞 **추가 도움이 필요한 경우**

각 서비스별 상세 가이드:
- 🤖 [Discord 설정 가이드](./discord-setup.md)
- 🗄️ [Supabase 설정 가이드](./supabase-setup.md)
- 🚀 [배포 가이드](../DEPLOYMENT.md) 