"""
Catcher Link 2: 설계평가
Design Effectiveness Testing - snowball link6 기반
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from catcher_auth import (
    login_required, get_current_user, get_user_rcms,
    get_rcm_details, get_rcm_info, has_rcm_access,
    log_user_activity, get_db
)

bp_link2 = Blueprint('design', __name__, url_prefix='/design')


def get_user_info():
    """현재 로그인한 사용자 정보 반환"""
    return get_current_user()


def is_logged_in():
    """로그인 상태 확인"""
    return 'user_info' in session


@bp_link2.route('/')
@bp_link2.route('/evaluation')
@login_required
def design_evaluation():
    """설계평가 메인 페이지 - RCM 선택"""
    user_info = get_user_info()

    # 사용자가 접근 가능한 RCM 목록 조회
    user_rcms = get_user_rcms(user_info['user_id'])

    # 카테고리별로 분류
    rcms_by_category = {
        'ELC': [rcm for rcm in user_rcms if rcm.get('control_category') == 'ELC'],
        'TLC': [rcm for rcm in user_rcms if rcm.get('control_category') == 'TLC'],
        'ITGC': [rcm for rcm in user_rcms if rcm.get('control_category') == 'ITGC']
    }

    log_user_activity(user_info, 'PAGE_ACCESS', '설계평가',
                     '/design/evaluation', request.remote_addr,
                     request.headers.get('User-Agent'))

    return render_template('design/design_evaluation.html',
                         rcms_by_category=rcms_by_category,
                         user_rcms=user_rcms,
                         is_logged_in=is_logged_in(),
                         user_info=user_info)


@bp_link2.route('/rcm', methods=['GET', 'POST'])
@login_required
def design_evaluation_rcm():
    """설계평가 RCM 상세 페이지"""
    user_info = get_user_info()

    # POST로 전달된 RCM ID 받기 또는 세션에서 가져오기
    if request.method == 'POST':
        rcm_id = request.form.get('rcm_id')
        if not rcm_id:
            flash('RCM 정보가 없습니다.', 'error')
            return redirect(url_for('design.design_evaluation'))

        # 세션에 저장
        session['current_design_rcm_id'] = int(rcm_id)
    else:
        # GET 요청인 경우 세션에서 가져오기
        rcm_id = session.get('current_design_rcm_id')
        if not rcm_id:
            flash('RCM 정보가 없습니다. 다시 선택해주세요.', 'error')
            return redirect(url_for('design.design_evaluation'))

    # 접근 권한 확인
    if not has_rcm_access(user_info['user_id'], rcm_id):
        flash('해당 RCM에 대한 접근 권한이 없습니다.', 'error')
        return redirect(url_for('design.design_evaluation'))

    # RCM 정보 조회
    rcm_info = get_rcm_info(rcm_id)
    if not rcm_info:
        flash('RCM을 찾을 수 없습니다.', 'error')
        return redirect(url_for('design.design_evaluation'))

    # RCM 세부 데이터 조회
    rcm_details = get_rcm_details(rcm_id)

    # 평가 세션 목록 조회
    evaluation_sessions = get_evaluation_sessions(rcm_id, user_info['user_id'])

    log_user_activity(user_info, 'PAGE_ACCESS', 'RCM 설계평가',
                     '/design/rcm', request.remote_addr,
                     request.headers.get('User-Agent'))

    return render_template('design/design_rcm_detail.html',
                         rcm_id=rcm_id,
                         rcm_info=rcm_info,
                         rcm_details=rcm_details,
                         evaluation_sessions=evaluation_sessions,
                         is_logged_in=is_logged_in(),
                         user_info=user_info)


@bp_link2.route('/api/save', methods=['POST'])
@login_required
def save_design_evaluation_api():
    """설계평가 결과 저장 API"""
    user_info = get_user_info()

    data = request.get_json()
    rcm_id = data.get('rcm_id')
    control_code = data.get('control_code')
    evaluation_data = data.get('evaluation_data')
    evaluation_session = data.get('evaluation_session')

    # 필수 데이터 검증
    if not all([rcm_id, control_code, evaluation_data, evaluation_session]):
        return jsonify({
            'success': False,
            'message': '필수 데이터가 누락되었습니다.'
        })

    try:
        # 접근 권한 확인
        if not has_rcm_access(user_info['user_id'], rcm_id):
            return jsonify({
                'success': False,
                'message': '해당 RCM에 대한 접근 권한이 없습니다.'
            })

        # 평가 데이터 저장
        save_design_evaluation_data(
            rcm_id=rcm_id,
            control_code=control_code,
            user_id=user_info['user_id'],
            session_name=evaluation_session,
            evaluation_data=evaluation_data
        )

        log_user_activity(user_info, 'DESIGN_EVAL_SAVE',
                        f'설계평가 저장 - {control_code}',
                        '/design/api/save', request.remote_addr,
                        request.headers.get('User-Agent'),
                        {'rcm_id': rcm_id, 'control_code': control_code})

        return jsonify({
            'success': True,
            'message': '설계평가가 저장되었습니다.'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'저장 중 오류가 발생했습니다: {str(e)}'
        }), 500


@bp_link2.route('/api/sessions/<int:rcm_id>')
@login_required
def get_evaluation_sessions_api(rcm_id):
    """평가 세션 목록 조회 API"""
    user_info = get_user_info()

    # 접근 권한 확인
    if not has_rcm_access(user_info['user_id'], rcm_id):
        return jsonify({
            'success': False,
            'message': '접근 권한이 없습니다.'
        }), 403

    try:
        sessions = get_evaluation_sessions(rcm_id, user_info['user_id'])

        return jsonify({
            'success': True,
            'sessions': sessions
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'세션 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500


@bp_link2.route('/api/create-session', methods=['POST'])
@login_required
def create_evaluation_session_api():
    """새 평가 세션 생성 API"""
    user_info = get_user_info()

    data = request.get_json()
    rcm_id = data.get('rcm_id')
    session_name = data.get('session_name')

    if not all([rcm_id, session_name]):
        return jsonify({
            'success': False,
            'message': '필수 데이터가 누락되었습니다.'
        })

    try:
        # 접근 권한 확인
        if not has_rcm_access(user_info['user_id'], rcm_id):
            return jsonify({
                'success': False,
                'message': '접근 권한이 없습니다.'
            })

        # 세션 생성
        session_id = create_design_evaluation_session(
            rcm_id=rcm_id,
            user_id=user_info['user_id'],
            session_name=session_name
        )

        log_user_activity(user_info, 'DESIGN_EVAL_SESSION_CREATE',
                        f'설계평가 세션 생성 - {session_name}',
                        '/design/api/create-session', request.remote_addr,
                        request.headers.get('User-Agent'),
                        {'rcm_id': rcm_id, 'session_name': session_name})

        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': '평가 세션이 생성되었습니다.'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'세션 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500


# Helper functions
def get_evaluation_sessions(rcm_id, user_id):
    """평가 세션 목록 조회"""
    with get_db() as conn:
        # 관리자인지 확인
        user = conn.execute('SELECT admin_flag FROM ca_user WHERE user_id = ?', (user_id,)).fetchone()
        is_admin = user and user['admin_flag'] == 'Y'

        if is_admin:
            # 관리자는 모든 세션 조회
            sessions = conn.execute('''
                SELECT header_id, evaluation_session as session_name,
                       evaluation_status, start_date as created_date,
                       total_controls, evaluated_controls, progress_percentage
                FROM ca_design_evaluation_header
                WHERE rcm_id = ?
                ORDER BY start_date DESC
            ''', (rcm_id,)).fetchall()
        else:
            # 일반 사용자는 본인 세션만 조회
            sessions = conn.execute('''
                SELECT header_id, evaluation_session as session_name,
                       evaluation_status, start_date as created_date,
                       total_controls, evaluated_controls, progress_percentage
                FROM ca_design_evaluation_header
                WHERE rcm_id = ? AND user_id = ?
                ORDER BY start_date DESC
            ''', (rcm_id, user_id)).fetchall()

        return [dict(session) for session in sessions]


def save_design_evaluation_data(rcm_id, control_code, user_id, session_name, evaluation_data):
    """설계평가 데이터 저장"""
    with get_db() as conn:
        # 헤더 ID 조회 또는 생성
        header = conn.execute('''
            SELECT header_id FROM ca_design_evaluation_header
            WHERE rcm_id = ? AND user_id = ? AND evaluation_session = ?
        ''', (rcm_id, user_id, session_name)).fetchone()

        if not header:
            # 헤더가 없으면 생성
            cursor = conn.execute('''
                INSERT INTO ca_design_evaluation_header
                (rcm_id, user_id, evaluation_session, evaluation_status)
                VALUES (?, ?, ?, 'IN_PROGRESS')
            ''', (rcm_id, user_id, session_name))
            header_id = cursor.lastrowid
        else:
            header_id = header['header_id']

        # 라인 데이터 저장
        existing = conn.execute('''
            SELECT line_id FROM ca_design_evaluation_line
            WHERE header_id = ? AND control_code = ?
        ''', (header_id, control_code)).fetchone()

        if existing:
            # 업데이트
            conn.execute('''
                UPDATE ca_design_evaluation_line
                SET description_adequacy = ?,
                    improvement_suggestion = ?,
                    overall_effectiveness = ?,
                    evaluation_rationale = ?,
                    recommended_actions = ?,
                    evaluation_date = CURRENT_TIMESTAMP,
                    last_updated = CURRENT_TIMESTAMP
                WHERE line_id = ?
            ''', (
                evaluation_data.get('description_adequacy'),
                evaluation_data.get('improvement_suggestion'),
                evaluation_data.get('overall_effectiveness'),
                evaluation_data.get('evaluation_rationale'),
                evaluation_data.get('recommended_actions'),
                existing['line_id']
            ))
        else:
            # 신규 삽입
            conn.execute('''
                INSERT INTO ca_design_evaluation_line
                (header_id, control_code, description_adequacy, improvement_suggestion,
                 overall_effectiveness, evaluation_rationale, recommended_actions, evaluation_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                header_id, control_code,
                evaluation_data.get('description_adequacy'),
                evaluation_data.get('improvement_suggestion'),
                evaluation_data.get('overall_effectiveness'),
                evaluation_data.get('evaluation_rationale'),
                evaluation_data.get('recommended_actions')
            ))

        # 헤더의 진행률 업데이트
        conn.execute('''
            UPDATE ca_design_evaluation_header
            SET last_updated = CURRENT_TIMESTAMP
            WHERE header_id = ?
        ''', (header_id,))

        conn.commit()


def create_design_evaluation_session(rcm_id, user_id, session_name):
    """설계평가 세션 생성"""
    with get_db() as conn:
        # RCM의 총 통제 수 조회
        total_controls = conn.execute('''
            SELECT COUNT(*) as cnt FROM ca_rcm_detail WHERE rcm_id = ?
        ''', (rcm_id,)).fetchone()['cnt']

        # 세션 헤더 생성
        cursor = conn.execute('''
            INSERT INTO ca_design_evaluation_header
            (rcm_id, user_id, evaluation_session, evaluation_status, total_controls)
            VALUES (?, ?, ?, 'IN_PROGRESS', ?)
        ''', (rcm_id, user_id, session_name, total_controls))
        header_id = cursor.lastrowid
        conn.commit()

        return header_id
