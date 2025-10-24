# Catcher - 내부회계관리제도(ICFR) 통합 관리 시스템

내부회계관리제도의 RCM 등록, 설계평가, 운영평가를 통합 관리하는 웹 애플리케이션입니다.

## 주요 기능

### 1. RCM (Risk and Control Matrix) 관리
- **개별 업로드**: ELC, TLC, ITGC 중 하나의 카테고리 선택하여 업로드
- **통합 업로드**: 하나의 Excel 파일로 여러 카테고리 동시 업로드
- **자동 컬럼 매핑**: Excel 헤더를 자동으로 DB 필드에 매핑
- **카테고리별 관리**: ELC/TLC/ITGC 분류 및 관리
- **권한 관리**: 사용자별 RCM 접근 권한 설정

### 2. 설계평가 (Design Effectiveness)
- **RCM 선택**: ELC/TLC/ITGC RCM 선택하여 평가 시작
- **평가 세션 관리**: 여러 평가 세션 생성 및 관리
- **통제 평가**: 통제별 설계 효과성 평가 및 기록
- **개선 제안**: 통제 개선 사항 및 권장 조치 문서화

### 3. 운영평가 (Operating Effectiveness)
- **설계평가 기반**: 완료된 설계평가 세션 선택
- **샘플 테스트**: 샘플 수 및 예외 건수 기록
- **테스트 결과**: 효과적/미비/미테스트 분류
- **발견사항 관리**: 테스트 절차 및 발견사항 문서화

### 4. 통합 대시보드
- 개발 예정

## 기술 스택

- **Backend**: Flask 2.3+
- **Database**: SQLite (snowball.db 기반)
- **Frontend**: Bootstrap 5, Jinja2
- **Excel Processing**: openpyxl
- **Testing**: pytest, pytest-mock

## 설치 및 실행

### 1. 필수 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 데이터베이스 준비

snowball.db를 catcher.db로 복사:

```bash
cp ../snowball/snowball.db catcher.db
```

또는 기존 catcher.db 사용

### 3. 서버 실행

```bash
python3 catcher.py
```

서버 주소: http://localhost:5001

### 4. 관리자 로그인

로컬호스트에서 실행 시 "관리자 로그인" 버튼으로 직접 로그인 가능

## 프로젝트 구조

```
catcher/
├── catcher.py              # 메인 애플리케이션
├── catcher_auth.py         # 인증 및 권한 관리 (공통)
├── catcher_link1.py        # Link 1: RCM 관리 (업로드/조회/삭제)
├── catcher_link2.py        # Link 2: 설계평가 (Design Effectiveness)
├── catcher_link3.py        # Link 3: 운영평가 (Operating Effectiveness)
├── catcher_link4.py        # Link 4: 대시보드 (개발 예정)
├── catcher.db              # SQLite 데이터베이스
├── requirements.txt         # Python 패키지 의존성
├── README.md               # 프로젝트 문서
├── CHANGELOG.md            # 변경 이력
│
├── templates/              # Jinja2 템플릿
│   ├── base.html          # 기본 템플릿
│   ├── index.html         # 메인 페이지
│   ├── login.html         # 로그인 페이지
│   ├── rcm/               # RCM 템플릿
│   │   ├── rcm_list.html
│   │   ├── rcm_upload.html
│   │   └── rcm_view.html
│   ├── design/            # 설계평가 템플릿
│   │   ├── design_evaluation.html
│   │   └── design_rcm_detail.html
│   └── operation/         # 운영평가 템플릿
│       ├── operation_evaluation.html
│       └── operation_rcm_detail.html
│
├── static/                # 정적 파일
│   └── uploads/          # 업로드된 파일
│
├── tests/                # 테스트 코드
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_rcm_upload.py
│
└── itgc/                 # Snowball 참조 코드 (보관용)
    └── ...
```

### 모듈 구성 (Link 기반)

- **catcher_auth.py**: 공통 인증 모듈
  - 사용자 인증, RCM 권한 관리
  - DB 연결 및 헬퍼 함수

- **catcher_link1.py**: RCM 관리
  - RCM 업로드 (개별/통합)
  - RCM 목록 조회 및 상세 보기
  - RCM 삭제 및 권한 관리

- **catcher_link2.py**: 설계평가
  - 평가 세션 생성 및 관리
  - 통제별 설계 효과성 평가
  - 평가 결과 저장

- **catcher_link3.py**: 운영평가
  - 설계평가 기반 운영 테스트
  - 샘플 테스트 기록
  - 테스트 결과 및 발견사항 저장

- **catcher_link4.py**: 대시보드 (개발 예정)
  - 통합 대시보드 및 리포팅

## 데이터베이스 스키마

### sb_user
사용자 정보

| 컬럼 | 타입 | 설명 |
|------|------|------|
| user_id | INTEGER | 기본키 |
| user_email | TEXT | 이메일 (고유) |
| user_name | TEXT | 사용자명 |
| company_name | TEXT | 회사명 |
| admin_flag | TEXT | 관리자 여부 (Y/N) |

### sb_rcm
RCM 정보

| 컬럼 | 타입 | 설명 |
|------|------|------|
| rcm_id | INTEGER | 기본키 |
| rcm_name | TEXT | RCM명 |
| control_category | TEXT | 카테고리 (ELC/TLC/ITGC) |
| description | TEXT | 설명 |
| upload_user_id | INTEGER | 업로드 사용자 ID |
| upload_date | TIMESTAMP | 업로드 일시 |

### sb_rcm_detail
RCM 상세 (통제 목록)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| detail_id | INTEGER | 기본키 |
| rcm_id | INTEGER | RCM ID (외래키) |
| control_code | TEXT | 통제코드 |
| control_name | TEXT | 통제명 |
| control_description | TEXT | 통제설명 |
| key_control | TEXT | 핵심통제 여부 |

### sb_user_rcm
사용자별 RCM 접근 권한

| 컬럼 | 타입 | 설명 |
|------|------|------|
| mapping_id | INTEGER | 기본키 |
| user_id | INTEGER | 사용자 ID (외래키) |
| rcm_id | INTEGER | RCM ID (외래키) |
| permission_type | TEXT | 권한 타입 (READ/WRITE) |

## RCM 업로드 가이드

### 개별 업로드

1. 관리자로 로그인
2. RCM → 업로드
3. "개별 업로드" 선택
4. 카테고리 선택 (ELC/TLC/ITGC)
5. Excel 파일 업로드

**Excel 형식:**
```
통제코드 | 통제명 | 통제설명 | 핵심통제여부 | 통제빈도
ITGC-001 | 시스템 접근 통제 | ... | Y | 연간
ITGC-002 | 변경 관리 | ... | Y | 수시
```

### 통합 업로드

1. 관리자로 로그인
2. RCM → 업로드
3. "통합 업로드" 선택
4. Excel 파일 업로드 (카테고리 컬럼 포함)

**Excel 형식:**
```
카테고리 | 통제코드 | 통제명 | 통제설명
ELC | ELC-001 | 이사회 운영 | ...
ELC | ELC-002 | 내부감사 | ...
TLC | TLC-001 | 매출 승인 | ...
ITGC | ITGC-001 | 시스템 접근 통제 | ...
```

통합 업로드 시 자동으로 다음과 같이 RCM이 생성됩니다:
- "RCM명 - ELC"
- "RCM명 - TLC"
- "RCM명 - ITGC"

### 자동 컬럼 매핑

다음 키워드를 포함한 Excel 헤더는 자동으로 매핑됩니다:

- **통제코드**: 통제코드, 코드, control code
- **통제명**: 통제명, 통제이름, control name
- **통제설명**: 통제설명, 설명, description
- **핵심통제**: 핵심통제, 핵심통제여부, key control
- **통제빈도**: 빈도, 통제빈도, frequency
- **카테고리** (통합 업로드): 카테고리, category, 구분

## 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_rcm_upload.py

# 특정 테스트 클래스 실행
pytest tests/test_rcm_upload.py::TestIndividualUpload

# 상세 출력
pytest -v

# 커버리지 확인
pytest --cov=. --cov-report=html
```

## 테스트 커버리지

- ✅ RCM 개별 업로드 (ELC/TLC/ITGC)
- ✅ RCM 통합 업로드 (여러 카테고리 동시 업로드)
- ✅ 자동 컬럼 매핑
- ✅ 카테고리 컬럼 감지
- ✅ 업로드 유효성 검증
- ✅ 사용자 권한 관리
- ✅ 로그인/로그아웃
- ✅ 세션 관리
- ✅ RCM 접근 제어

## 보안

- **인증**: 세션 기반 인증
- **권한**: 관리자/일반 사용자 구분
- **세션**: 브라우저 종료 시 자동 만료
- **활동 로그**: 모든 사용자 활동 기록
- **안전한 리다이렉트**: URL 검증을 통한 Open Redirect 방지

## 향후 계획

- [ ] 컬럼 매핑 UI 페이지
- [ ] RCM 수정/삭제 기능
- [ ] Excel 다운로드 기능
- [ ] 설계평가 모듈
- [ ] 운영평가 모듈
- [ ] 통합 대시보드
- [ ] OTP 이메일 인증
- [ ] 사용자 관리 페이지

## 라이선스

내부 사용 전용

## 문의

프로젝트 관련 문의사항은 이슈로 등록해주세요.
