"""
Catcher - 내부회계관리제도(ICFR) 통합 관리 시스템
메인 진입점
"""

from flask import Flask, render_template, redirect, url_for, session, request, flash
import os
import sys

# Catcher 루트 경로를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'catcher_secret_key_150606')

# 설정
app.config['DEBUG'] = True
app.config['JSON_AS_ASCII'] = False  # 한글 지원

# 세션 설정 - 브라우저 종료 시 만료
app.config.update(
    SESSION_COOKIE_SECURE=False,  # 로컬 개발환경
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# Blueprint 등록 (Link 기반 구조)
from catcher_link1 import bp_link1  # RCM 관리
from catcher_link2 import bp_link2  # 설계평가
from catcher_link3 import bp_link3  # 운영평가

app.register_blueprint(bp_link1)
app.register_blueprint(bp_link2)
app.register_blueprint(bp_link3)

# 데이터베이스 경로
DB_PATH = os.path.join(os.path.dirname(__file__), 'catcher.db')

# 앱 컨텍스트에서 DB 연결 관리
@app.teardown_appcontext
def close_db(error):
    """요청 종료 시 DB 연결 닫기"""
    from catcher_auth import close_db
    close_db(error)

def is_logged_in():
    """로그인 상태 확인 함수"""
    from catcher_auth import get_current_user
    return 'user_id' in session and get_current_user() is not None

def get_user_info():
    """현재 로그인한 사용자 정보 반환"""
    if is_logged_in():
        if 'user_info' in session:
            return session['user_info']
        from catcher_auth import get_current_user
        return get_current_user()
    return None

@app.route('/')
def index():
    """메인 화면 - RCM, 설계평가, 운영평가, 대시보드 카드 표시"""
    return render_template('index.html')

# 로그인/로그아웃
@app.route('/login', methods=['GET', 'POST'])
def login():
    """로그인 페이지 (Snowball 방식)"""
    from catcher_auth import authenticate_user, get_db
    from datetime import datetime
    from urllib.parse import urlparse, urljoin

    # next 파라미터 처리
    next_page = request.args.get('next')

    # 안전한 리다이렉트를 위한 검증
    def is_safe_url(target):
        ref_url = urlparse(request.host_url)
        test_url = urlparse(urljoin(request.host_url, target))
        return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

    action = None
    if request.method == 'POST':
        action = request.form.get('action')

    if action == 'admin_login':
        # 관리자 로그인 (로컬호스트만)
        client_ip = request.environ.get('REMOTE_ADDR', '')

        if client_ip == '127.0.0.1':
            with get_db() as conn:
                user = conn.execute(
                    'SELECT * FROM ca_user WHERE admin_flag = ? AND (effective_end_date IS NULL OR effective_end_date > CURRENT_TIMESTAMP)',
                    ('Y',)
                ).fetchone()

                if user:
                    user_dict = dict(user)
                    session['user_id'] = user_dict['user_id']
                    session['user_email'] = user_dict['user_email']
                    session['user_info'] = {
                        'user_id': user_dict['user_id'],
                        'user_name': user_dict['user_name'],
                        'user_email': user_dict['user_email'],
                        'company_name': user_dict.get('company_name', ''),
                        'admin_flag': user_dict.get('admin_flag', 'N')
                    }
                    session['last_activity'] = datetime.now().isoformat()

                    # next 파라미터가 있으면 해당 페이지로, 없으면 index로
                    if next_page and is_safe_url(next_page):
                        return redirect(next_page)
                    return redirect(url_for('index'))
                else:
                    return render_template('login.html', error="관리자 계정을 찾을 수 없습니다.", remote_addr=request.remote_addr, next=next_page)
        else:
            return render_template('login.html', error="관리자 로그인은 로컬호스트에서만 가능합니다.", remote_addr=request.remote_addr, next=next_page)

    # GET 요청 또는 다른 action
    return render_template('login.html', remote_addr=request.remote_addr, next=next_page)

@app.route('/logout')
def logout():
    """로그아웃"""
    session.clear()
    return redirect(url_for('index'))

# RCM 모듈 라우트는 Blueprint에서 처리
# /rcm은 rcm.rcm_list로 자동 연결됨

# 설계평가 모듈 라우트 - Blueprint에서 처리
# /design은 design.design_evaluation으로 자동 연결됨

# 운영평가 모듈 라우트 - Blueprint에서 처리
# /operation은 operation.operation_evaluation으로 자동 연결됨

# 대시보드 라우트
@app.route('/dashboard')
def dashboard():
    """통합 대시보드"""
    return render_template('dashboard.html')

# 에러 핸들러
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # 템플릿 및 static 폴더 확인
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    static_dir = os.path.join(os.path.dirname(__file__), 'static')

    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
        print(f"✓ templates 폴더 생성: {template_dir}")

    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        print(f"✓ static 폴더 생성: {static_dir}")

    # 데이터베이스 확인
    if not os.path.exists(DB_PATH):
        print(f"⚠️  경고: 데이터베이스 파일이 없습니다: {DB_PATH}")
        print("   snowball.db를 복사하여 catcher.db로 만들어주세요.")
    else:
        print(f"✓ 데이터베이스 연결: {DB_PATH}")

    print("=" * 60)
    print("🛡️  Catcher - 내부회계관리제도 통합 관리 시스템")
    print("=" * 60)
    print(f"🌐 서버 주소: http://localhost:5001")
    print(f"📁 템플릿 경로: {template_dir}")
    print(f"📁 정적 파일 경로: {static_dir}")
    print(f"💾 데이터베이스: {DB_PATH}")
    print("=" * 60)
    print("📝 RCM 모듈: ELC, TLC, ITGC 등록 및 관리")
    print("📝 설계평가: 통제 설계 효과성 평가")
    print("📝 운영평가: 통제 운영 효과성 평가")
    print("📝 대시보드: 개발 예정")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5001, debug=True)
