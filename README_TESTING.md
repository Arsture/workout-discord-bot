# 테스트 가이드

## 개요

이 프로젝트는 pytest를 사용한 체계적인 테스트 시스템을 구축했습니다. 기존의 SQLite 기반 테스트 코드에서 실제 Supabase를 사용하는 현대적인 테스트 구조로 전환했습니다.

## 테스트 구조

```
tests/
├── __init__.py           # 테스트 패키지
├── conftest.py          # pytest 설정 및 공통 fixture
├── test_models.py       # 도메인 모델 단위 테스트
├── test_services.py     # 서비스 레이어 단위 테스트
├── test_utils.py        # 유틸리티 함수 단위 테스트
└── test_integration.py  # 통합 테스트 (실제 Supabase 연결)
```

## 테스트 유형

### 1. 단위 테스트 (Unit Tests)
- **마커**: `@pytest.mark.unit`
- **특징**: Mock을 사용한 빠른 테스트
- **파일**: `test_models.py`, `test_services.py`, `test_utils.py`

### 2. 통합 테스트 (Integration Tests)  
- **마커**: `@pytest.mark.integration`
- **특징**: 실제 Supabase 데이터베이스 연결 필요
- **파일**: `test_integration.py`

## 테스트 실행 방법

### 전체 테스트 실행
```bash
pytest
```

### 단위 테스트만 실행 (빠름)
```bash
pytest -m unit
```

### 통합 테스트만 실행 (Supabase 환경변수 필요)
```bash
pytest -m integration
```

### 특정 파일 테스트
```bash
pytest tests/test_models.py
pytest tests/test_services.py
```

### 특정 테스트 클래스/함수 실행
```bash
pytest tests/test_models.py::TestUserSettings
pytest tests/test_services.py::TestPenaltyService::test_calculate_penalty_goal_achieved
```

### 상세 출력으로 실행
```bash
pytest -v
```

### 커버리지 포함 실행
```bash
pytest --cov=. --cov-report=html
```

## 환경 설정

### 단위 테스트
추가 설정 없이 실행 가능합니다. Mock을 사용하여 외부 의존성을 제거했습니다.

### 통합 테스트
실제 Supabase 환경변수가 필요합니다:

```bash
export SUPABASE_URL="your_supabase_url"
export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"
```

또는 `.env` 파일에 설정:
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### 테스트용 환경변수
통합 테스트가 아닌 경우, `conftest.py`에서 자동으로 테스트용 환경변수를 설정합니다.

## 주요 Fixture

### 도메인 모델 Fixture
- `sample_user_settings`: 테스트용 사용자 설정
- `sample_workout_record`: 테스트용 운동 기록  
- `sample_weekly_progress`: 테스트용 주간 진행 상황

### 서비스 Fixture
- `penalty_service`: PenaltyService 인스턴스
- `workout_service`: WorkoutService 인스턴스 (Mock DB 포함)
- `report_service`: ReportService 인스턴스 (Mock DB 포함)

### 데이터베이스 Fixture
- `mock_database`: Mock된 Database 인스턴스
- `mock_supabase_client`: Mock된 Supabase 클라이언트

## 테스트 작성 가이드

### 1. 단위 테스트 작성

```python
import pytest
from services import PenaltyService

class TestPenaltyService:
    def test_calculate_penalty(self, penalty_service):
        """벌금 계산 테스트"""
        penalty = penalty_service.calculate_penalty(5, 3)
        assert penalty == 2880  # (5-3) * 1440
```

### 2. 비동기 테스트 작성

```python
@pytest.mark.asyncio
async def test_async_function(workout_service, mock_database):
    """비동기 함수 테스트"""
    mock_database.get_user_settings = AsyncMock(return_value=None)
    
    result = await workout_service.add_workout_record(123, "테스트")
    assert result['success'] is False
```

### 3. Mock 사용

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mock(workout_service, mock_database):
    # 데이터베이스 Mock 설정
    mock_database.set_user_goal = AsyncMock(return_value=True)
    
    # 외부 함수 Mock
    with patch('utils.get_week_start_end') as mock_get_week:
        mock_get_week.return_value = (datetime.now(), datetime.now())
        result = await workout_service.set_user_goal(123, "테스트", 5)
    
    assert result['success'] is True
```

## 테스트 실행 예시

### 개발 중 빠른 테스트
```bash
# 단위 테스트만 실행 (빠름)
pytest -m unit

# 특정 서비스만 테스트
pytest tests/test_services.py::TestPenaltyService -v
```

### CI/CD 환경
```bash
# 모든 테스트 실행 (통합 테스트 제외)
pytest -m "not integration"

# 커버리지 포함 전체 테스트
pytest --cov=. --cov-report=xml --cov-fail-under=80
```

### 통합 테스트 (환경변수 있을 때만)
```bash
# 실제 Supabase 연결 테스트
pytest -m integration -v
```

## 기존 test_bot.py와의 차이점

| 구분 | 기존 test_bot.py | 새로운 pytest 시스템 |
|------|------------------|---------------------|
| 데이터베이스 | SQLite | Supabase (Mock + 실제) |
| 테스트 프레임워크 | 단순 print | pytest |
| 검증 방식 | 눈으로 확인 | assert 문 |
| 테스트 분리 | 하나의 파일 | 레이어별 분리 |
| Mock 지원 | 없음 | 완전한 Mock 지원 |
| 병렬 실행 | 불가능 | 가능 |
| 커버리지 | 없음 | 자동 측정 |

## 권장 워크플로

1. **개발 중**: `pytest -m unit` (빠른 피드백)
2. **커밋 전**: `pytest -m "not integration"` (단위 + 일부 통합)
3. **배포 전**: `pytest` (전체 테스트)
4. **성능 테스트**: `pytest -m integration` (실제 환경)

## 문제 해결

### 테스트가 실패하는 경우
1. 환경변수 확인 (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`)
2. 의존성 설치 확인 (`poetry install`)
3. Mock 설정 확인
4. 비동기 테스트 마커 확인 (`@pytest.mark.asyncio`)

### 느린 테스트
- 단위 테스트만 실행: `pytest -m unit`
- 병렬 실행: `pytest -n auto` (pytest-xdist 필요)

### 통합 테스트 실패
- Supabase 연결 확인
- 테스트용 사용자 ID 충돌 확인 (999999999번대 사용)
- 네트워크 연결 상태 확인 