# Sentinel RCM 모듈 구현 완료 보고서

**작성일**: 2024-10-24
**프로젝트**: Sentinel - 내부회계관리제도 통합 관리 시스템
**모듈**: RCM (Risk and Control Matrix) 업로드 및 관리

---

## 🎯 구현 목표

기존 Snowball(ITGC 전용)을 확장하여 ELC, TLC, ITGC를 통합 관리할 수 있는 Sentinel 시스템 구축.
**1차 목표: RCM 업로드 및 관리 기능 구현**

---

## ✅ 완료된 작업

### 1. 데이터베이스 통합
- **snowball.db → sentinel.db** 복사
- 기존 사용자, RCM 데이터 모두 보존
- `sb_rcm` 테이블에 `control_category` 컬럼 추가
  ```sql
  ALTER TABLE sb_rcm ADD COLUMN control_category TEXT DEFAULT 'ITGC';
  ```

### 2. 인증 시스템 통합
- Snowball의 `sb_user`, `sb_user_rcm` 테이블 활용
- 사용자 인증 및 권한 관리 시스템 연동
- 관리자/일반 사용자 권한 구분

### 3. RCM 모듈 구현

#### 3.1 RCM 업로드 (관리자 전용)
- **URL**: `/rcm/upload`
- **기능**:
  - Excel 파일(.xlsx, .xls) 업로드
  - ELC/TLC/ITGC 카테고리 선택
  - 자동 컬럼 매핑 (한글/영문 헤더 자동 인식)
  - 대상 사용자에게 자동 권한 부여

#### 3.2 RCM 목록 조회
- **URL**: `/rcm/list` (전체), `/rcm/ELC`, `/rcm/TLC`, `/rcm/ITGC`
- **기능**:
  - 카테고리별 탭 UI
  - 업로드 일자, 회사명, 권한 표시
  - 관리자: 모든 RCM 조회 가능
  - 일반 사용자: 권한이 부여된 RCM만 조회

#### 3.3 RCM 상세 조회
- **URL**: `/rcm/<rcm_id>/view`
- **기능**:
  - RCM 기본 정보 (이름, 설명, 업로드 정보)
  - 통제 목록 테이블 (통제코드, 통제명, 설명, 핵심통제, 빈도 등)
  - Excel 내보내기 버튼 (준비)

### 4. 자동 컬럼 매핑 규칙

| DB 필드 | 인식 키워드 |
|---------|------------|
| control_code | 통제코드, 코드, control code, code |
| control_name | 통제명, 통제이름, control name |
| control_description | 통제설명, 설명, description |
| key_control | 핵심통제, key control |
| control_frequency | 빈도, 통제빈도, frequency |
| control_type | 통제유형, 유형, type |
| control_nature | 통제성격, 성격, nature |

### 5. UI/UX
- Snowball 컬러 테마 적용
  - Primary: #2c3e50
  - Secondary: #3498db
- Bootstrap 5 기반 반응형 디자인
- 카테고리별 아이콘 및 그라데이션

---

## 📁 프로젝트 구조

```
sentinel/
├── sentinel.py              # 메인 진입점 (Port 5001)
├── sentinel.db              # Snowball 데이터 + control_category
├── rcm/                     # RCM 모듈
│   ├── __init__.py
│   └── routes.py           # RCM 라우트 (업로드, 목록, 상세)
├── common/
│   └── auth.py             # 인증 및 권한 (Snowball 스키마 사용)
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── rcm_home.html
│   └── rcm/
│       ├── rcm_list.html      # 카테고리별 탭 목록
│       ├── rcm_category.html  # 단일 카테고리 목록
│       ├── rcm_upload.html    # Excel 업로드
│       └── rcm_view.html      # RCM 상세
├── static/
│   └── css/
│       └── style.css       # Snowball 테마
├── docs/
│   ├── RCM_Upload_Template.md
│   └── IMPLEMENTATION_SUMMARY.md
└── itgc/                   # Snowball 원본 (참조용)
```

---

## 🌐 주요 URL

| URL | 기능 | 권한 |
|-----|------|------|
| http://localhost:5001 | 메인 페이지 | All |
| /rcm | RCM 홈 (ELC/TLC/ITGC 선택) | All |
| /rcm/list | 전체 RCM 목록 (탭) | 로그인 |
| /rcm/ELC | ELC RCM 목록 | 로그인 |
| /rcm/TLC | TLC RCM 목록 | 로그인 |
| /rcm/ITGC | ITGC RCM 목록 | 로그인 |
| /rcm/<id>/view | RCM 상세 조회 | 권한 보유자 |
| /rcm/upload | RCM Excel 업로드 | 관리자 |

---

## 🔑 핵심 기능 코드

### RCM 생성 (카테고리 포함)
```python
def create_rcm(rcm_name, control_category, description, upload_user_id, original_filename=None):
    db = get_db()
    cursor = db.execute('''
        INSERT INTO sb_rcm (rcm_name, control_category, description, upload_user_id, original_filename)
        VALUES (?, ?, ?, ?, ?)
    ''', (rcm_name, control_category, description, upload_user_id, original_filename))
    db.commit()
    return cursor.lastrowid
```

### 자동 컬럼 매핑
```python
def perform_auto_mapping(headers):
    mapping = {}
    mapping_rules = {
        'control_code': ['통제코드', '코드', 'control code', 'code'],
        'control_name': ['통제명', '통제이름', 'control name'],
        # ...
    }
    for db_field, keywords in mapping_rules.items():
        for idx, header in enumerate(headers):
            if any(keyword.lower() in header.lower() for keyword in keywords):
                mapping[db_field] = idx
                break
    return mapping
```

---

## 📊 데이터베이스 변경사항

### 추가된 컬럼
```sql
-- sb_rcm 테이블
ALTER TABLE sb_rcm ADD COLUMN control_category TEXT DEFAULT 'ITGC';
```

### 기존 데이터
- 5개의 RCM이 'ITGC' 카테고리로 자동 설정됨
- 사용자 및 권한 데이터 그대로 유지

---

## 🚀 실행 방법

```bash
cd /Users/newsistraphael/Pythons/sentinel
python3 sentinel.py
```

브라우저에서 http://localhost:5001 접속

---

## 📝 향후 개발 과제

### 단기 (RCM 모듈 완성)
1. ⬜ 로그인/회원가입 페이지 구현
2. ⬜ RCM Excel 내보내기 기능
3. ⬜ RCM 수정/삭제 기능
4. ⬜ 통제 상세 모달 구현

### 중기 (설계평가/운영평가)
1. ⬜ 설계평가 모듈 개발
2. ⬜ 운영평가 모듈 개발 (기존 ITGC snowball 통합)
3. ⬜ RCM → 평가 연동

### 장기 (통합 시스템)
1. ⬜ 대시보드 구현
2. ⬜ 보고서 생성
3. ⬜ AI 검토 기능 통합

---

## ⚠️ 주의사항

1. **데이터베이스 백업**
   - sentinel.db는 snowball.db의 복사본
   - 원본 snowball.db는 별도 보관

2. **포트 충돌**
   - Sentinel: 5001
   - Snowball: 5000 (기존)

3. **권한 관리**
   - 관리자만 RCM 업로드 가능
   - 일반 사용자는 부여된 RCM만 조회

---

## 📞 문의

내부 감사팀

---

**구현 완료일**: 2024-10-24
**최종 업데이트**: 2024-10-24
