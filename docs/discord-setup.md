# 🤖 Discord 봇 설정 가이드

## Discord 봇 토큰 얻기

### 1단계: Discord Developer Portal 접속
1. [Discord Developer Portal](https://discord.com/developers/applications) 접속
2. Discord 계정으로 로그인

### 2단계: 새 애플리케이션 생성
1. **"New Application"** 버튼 클릭
2. 애플리케이션 이름 입력 (예: "Workout Bot")
3. **"Create"** 버튼 클릭

### 3단계: 봇 생성
1. 왼쪽 메뉴에서 **"Bot"** 클릭
2. **"Add Bot"** 버튼 클릭
3. **"Yes, do it!"** 확인

### 4단계: 봇 토큰 복사
1. **"Token"** 섹션에서 **"Copy"** 버튼 클릭
2. 토큰을 안전한 곳에 저장 (이것이 `DISCORD_TOKEN`)

⚠️ **중요**: 토큰을 절대 공개하지 마세요!

### 5단계: 봇 권한 설정
**"Bot"** 페이지에서 다음 권한 활성화:
- ✅ **Send Messages**
- ✅ **Use Slash Commands** 
- ✅ **Read Message History**
- ✅ **Add Reactions**
- ✅ **Attach Files**

### 6단계: OAuth2 URL 생성
1. 왼쪽 메뉴에서 **"OAuth2"** → **"URL Generator"** 클릭
2. **Scopes** 선택:
   - ✅ `bot`
   - ✅ `applications.commands`
3. **Bot Permissions** 선택:
   - ✅ Send Messages
   - ✅ Use Slash Commands
   - ✅ Read Message History
   - ✅ Add Reactions
   - ✅ Attach Files
4. 생성된 URL로 봇을 서버에 초대

### 7단계: 서버 설정
1. Discord 서버에서 **"workout"** 채널 생성
2. **"Admin"** 역할 생성 (관리자용)
3. 봇에게 적절한 권한 부여 