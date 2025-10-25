# Catcher 변경 이력

## 2025-10-25
- 파비콘 추가 (index.html, base.html)
- 테스트 코드 개선: conftest.py department 컬럼 제거
- 테스트 추가: test_link2.py (설계평가), test_link3.py (운영평가)
- 테스트 통과: 45개 모두 통과
- GitHub 배포: https://github.com/Raphael-Yoon/catcher (master, developer 브랜치)
- 데이터베이스 테이블 접두사 변경: sb_ → ca_ (18개 테이블)
- Python 코드 업데이트: 14개 파일에서 116개 참조 변경
- 백업 생성: catcher.db.backup_before_rename

## 2025-10-24
- 시스템 이름 변경: Sentinel → Catcher (호밀밭의 파수꾼)
- Link 기반 파일 구조 정리 (link1: RCM, link2: 설계평가, link3: 운영평가, link4: 대시보드)
- Snowball 스타일 적용 (히어로 섹션, feature 카드, container 90% 너비)
- 이미지 추가 및 레이아웃 조정
- RCM 업로드 기능 구현 (개별/통합 업로드, 자동 컬럼 매핑)
- 세션 관리 및 로그인 리다이렉트 개선
