"""
RCM - Risk and Control Matrix (위험 및 통제 매트릭스)

주요 기능:
- 업무 프로세스별 위험 식별
- 통제 활동 정의 및 매핑
- RCM 문서 작성 및 관리
- 통제 번호 체계 관리

대상 영역:
- ITGC (IT General Controls)
- ELC (Entity Level Controls)
- TLC (Transaction Level Controls)
"""

from .routes import bp_rcm

__all__ = ['bp_rcm']
