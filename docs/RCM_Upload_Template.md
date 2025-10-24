# RCM Excel 업로드 템플릿 가이드

## 📋 필수 컬럼

Excel 파일의 첫 번째 행에 다음 컬럼 중 일부를 포함해야 합니다:

### 필수 컬럼 (반드시 포함)
- **통제코드** (control_code): 통제의 고유 식별자
- **통제명** (control_name): 통제 활동의 이름
- **통제설명** (control_description): 통제 활동의 상세 설명

### 권장 컬럼
- **핵심통제** (key_control): Y/N
- **통제빈도** (control_frequency): 일일, 주간, 월간, 분기, 연간 등
- **통제유형** (control_type): 예방/탐지/보정
- **통제성격** (control_nature): 자동/수동/반자동
- **프로세스** (process_area): 업무 영역
- **위험설명** (risk_description): 관련 위험 설명
- **모집단** (population): 테스트 모집단 설명
- **테스트절차** (test_procedure): 샘플링 및 테스트 방법

## 📁 파일 형식

- **지원 형식**: .xlsx, .xls
- **시트명**: 'RCM' (없으면 첫 번째 시트 사용)
- **헤더 위치**: 첫 번째 행

## 🎯 자동 매핑 키워드

시스템이 자동으로 인식하는 한글/영문 키워드:

| DB 필드 | 인식 키워드 |
|---------|------------|
| control_code | 통제코드, 코드, control code, code |
| control_name | 통제명, 통제이름, 통제활동, control name |
| control_description | 통제설명, 설명, 통제내용, description |
| key_control | 핵심통제, 핵심통제여부, key control |
| control_frequency | 빈도, 통제빈도, frequency |
| control_type | 통제유형, 유형, type |
| control_nature | 통제성격, 성격, nature |
| process_area | 프로세스, 업무영역, process |

## 📝 예시

```
통제코드 | 통제명 | 통제설명 | 핵심통제 | 빈도 | 유형
APD01-01 | 사용자 ID 발급 통제 | 신규 사용자 ID 발급 시... | Y | 월간 | 예방
APD01-02 | 접근 권한 검토 | 분기별 사용자 접근 권한... | Y | 분기 | 탐지
PC01-01 | 변경 요청 승인 | 모든 시스템 변경은... | Y | 건별 | 예방
```

## ⚙️ 업로드 프로세스

1. **RCM 업로드 페이지 접속** (관리자 전용)
   - URL: http://localhost:5001/rcm/upload

2. **정보 입력**
   - RCM명: 예) "2024년 재무보고 ITGC"
   - 카테고리 선택: ELC / TLC / ITGC
   - 설명: 선택사항
   - 대상 사용자: 접근 권한을 부여할 사용자

3. **Excel 파일 선택 및 업로드**
   - 파일 선택 후 "업로드" 버튼 클릭
   - 자동으로 컬럼 매핑 및 데이터 저장

4. **완료**
   - RCM 목록에서 업로드된 RCM 확인
   - 상세 보기에서 통제 목록 확인

## 🔒 권한

- **업로드**: 관리자(admin_flag='Y')만 가능
- **조회**: 권한이 부여된 사용자만 가능
- **카테고리**: ELC, TLC, ITGC로 구분 관리
