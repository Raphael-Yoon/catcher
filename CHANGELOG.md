# Sentinel 변경 이력

## 2025-10-24 - RCM 업로드 기능 구현

### 주요 기능 추가

#### 1. RCM 업로드 모드 선택
- **개별 업로드**: ELC, TLC, ITGC 중 하나의 카테고리만 선택하여 업로드
- **통합 업로드**: 하나의 Excel 파일에 여러 카테고리를 포함하여 업로드

#### 2. 개별 업로드 기능
- 사용자가 ELC/TLC/ITGC 중 하나를 선택
- Excel 파일을 업로드하면 해당 카테고리의 RCM이 생성됨
- 자동 컬럼 매핑으로 Excel 헤더를 DB 필드에 매핑

#### 3. 통합 업로드 기능
- Excel 파일에 "카테고리" 또는 "category" 컬럼 포함 필수
- 각 행마다 ELC/TLC/ITGC 값 지정
- 자동으로 카테고리별 RCM 생성
  - 예: "2024년 재무보고 RCM - ELC"
  - 예: "2024년 재무보고 RCM - TLC"
  - 예: "2024년 재무보고 RCM - ITGC"
- 각 RCM에 해당 카테고리의 통제만 저장

#### 4. 자동 컬럼 매핑
Excel 헤더를 다음 DB 필드에 자동 매핑:
- control_code: 통제코드, 코드, control code
- control_name: 통제명, 통제이름, control name
- control_description: 통제설명, 설명, description
- key_control: 핵심통제, 핵심통제여부, key control
- control_frequency: 빈도, 통제빈도, frequency
- control_type: 통제유형, 유형, type
- control_nature: 통제성격, 성격, nature
- population: 모집단
- test_procedure: 테스트절차, 절차, test
- 기타 위험 관련 필드들

#### 5. 보안 및 권한
- 관리자만 업로드 가능 (`@admin_required`)
- 대상 사용자에게 자동으로 READ 권한 부여
- 모든 업로드 활동이 로그에 기록됨

### 세션 관리 개선
- 브라우저 종료 시 세션 자동 만료
- `SESSION_COOKIE_MAX_AGE` 제거
- 보안 설정 유지 (HTTPONLY, SAMESITE)

### 로그인 후 리다이렉트 개선
- 로그아웃 상태에서 특정 페이지 접근 시 로그인 페이지로 이동
- 로그인 성공 후 원래 접근하려던 페이지로 자동 리다이렉트
- `next` 파라미터를 통한 안전한 URL 검증

### 파일 구조
```
sentinel/
├── sentinel.py              # 메인 애플리케이션 (포트 5001)
├── sentinel.db              # snowball.db 복사본
├── common/
│   └── auth.py             # 인증 및 권한 관리
├── rcm/
│   ├── __init__.py
│   └── routes.py           # RCM 업로드 로직
└── templates/
    ├── base.html           # 기본 템플릿
    ├── login.html          # 로그인 페이지
    ├── index.html          # 메인 페이지 (4개 카드)
    └── rcm/
        ├── rcm_list.html   # RCM 목록 (ELC/TLC/ITGC 탭)
        └── rcm_upload.html # RCM 업로드 (개별/통합 선택)
```

### 데이터베이스
- `sb_rcm` 테이블: control_category 컬럼으로 ELC/TLC/ITGC 구분
- `sb_rcm_detail` 테이블: 통제 상세 정보
- `sb_user_rcm` 테이블: 사용자별 RCM 접근 권한
- `sb_user_activity_log` 테이블: 모든 활동 로그

### 기술 스택
- Flask Blueprint 아키텍처
- SQLite (snowball.db 기반)
- Bootstrap 5
- openpyxl (Excel 파싱)
- Jinja2 템플릿

### 향후 계획
- [ ] 컬럼 매핑 UI 페이지 구현
- [ ] RCM 수정/삭제 기능
- [ ] Excel 다운로드 기능
- [ ] 설계평가 모듈 연동
- [ ] 운영평가 모듈 연동
- [ ] 통합 대시보드 구현
