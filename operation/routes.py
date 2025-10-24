"""
Operation Evaluation Routes
운영평가 라우트 - snowball link7 기반
"""
from flask import request, jsonify, render_template, redirect, url_for, flash, session
import sys
import os

# Sentinel 루트 경로를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operation import bp_operation
from common.auth import (
    login_required, get_current_user, get_user_rcms,
    get_rcm_details, get_rcm_info, has_rcm_access,
    log_user_activity, get_db
)


def get_user_info():
    """현재 로그인한 사용자 정보 반환"""
    return get_current_user()


def is_logged_in():
    """로그인 상태 확인"""
    return 'user_info' in session


@bp_operation.route('/')
@bp_operation.route('/evaluation')
@login_required
def operation_evaluation():
    """운영평가 메인 페이지 - RCM 선택"""
    user_info = get_user_info()

    # 사용자가 접근 가능한 RCM 목록 조회
    user_rcms = get_user_rcms(user_info['user_id'])

    # 카테고리별로 분류
    rcms_by_category = {
        'ELC': [rcm for rcm in user_rcms if rcm.get('control_category') == 'ELC'],
        'TLC': [rcm for rcm in user_rcms if rcm.get('control_category') == 'TLC'],
        'ITGC': [rcm for rcm in user_rcms if rcm.get('control_category') == 'ITGC']
    }

    log_user_activity(user_info, 'PAGE_ACCESS', '운영평가',
                     '/operation/evaluation', request.remote_addr,
                     request.headers.get('User-Agent'))

    return render_template('operation/operation_evaluation.html',
                         rcms_by_category=rcms_by_category,
                         user_rcms=user_rcms,
                         is_logged_in=is_logged_in(),
                         user_info=user_info)


@bp_operation.route('/rcm', methods=['GET', 'POST'])
@login_required
def operation_evaluation_rcm():
    """운영평가 RCM 상세 페이지"""
    user_info = get_user_info()

    # POST로 전달된 RCM ID 받기 또는 세션에서 가져오기
    if request.method == 'POST':
        rcm_id = request.form.get('rcm_id')
        if not rcm_id:
            flash('RCM 정보가 없습니다.', 'error')
            return redirect(url_for('operation.operation_evaluation'))

        # 세션에 저장
        session['current_operation_rcm_id'] = int(rcm_id)
    else:
        # GET 요청인 경우 세션에서 가져오기
        rcm_id = session.get('current_operation_rcm_id')
        if not rcm_id:
            flash('RCM 정보가 없습니다. 다시 선택해주세요.', 'error')
            return redirect(url_for('operation.operation_evaluation'))

    # 접근 권한 확인
    if not has_rcm_access(user_info['user_id'], rcm_id):
        flash('해당 RCM에 대한 접근 권한이 없습니다.', 'error')
        return redirect(url_for('operation.operation_evaluation'))

    # RCM 정보 조회
    rcm_info = get_rcm_info(rcm_id)
    if not rcm_info:
        flash('RCM을 찾을 수 없습니다.', 'error')
        return redirect(url_for('operation.operation_evaluation'))

    # RCM 세부 데이터 조회
    rcm_details = get_rcm_details(rcm_id)

    # 설계평가 세션 목록 조회 (운영평가는 설계평가 기반)
    design_sessions = get_design_sessions(rcm_id)

    log_user_activity(user_info, 'PAGE_ACCESS', 'RCM 운영평가',
                     '/operation/rcm', request.remote_addr,
                     request.headers.get('User-Agent'))

    return render_template('operation/operation_rcm_detail.html',
                         rcm_id=rcm_id,
                         rcm_info=rcm_info,
                         rcm_details=rcm_details,
                         design_sessions=design_sessions,
                         is_logged_in=is_logged_in(),
                         user_info=user_info)


@bp_operation.route('/api/save', methods=['POST'])
@login_required
def save_operation_evaluation_api():
    """운영평가 결과 저장 API"""
    user_info = get_user_info()

    data = request.get_json()
    rcm_id = data.get('rcm_id')
    control_code = data.get('control_code')
    design_session = data.get('design_session')
    evaluation_data = data.get('evaluation_data')

    # 필수 데이터 검증
    if not all([rcm_id, control_code, design_session, evaluation_data]):
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
        save_operation_evaluation_data(
            rcm_id=rcm_id,
            control_code=control_code,
            user_id=user_info['user_id'],
            design_session=design_session,
            evaluation_data=evaluation_data
        )

        log_user_activity(user_info, 'OPERATION_EVAL_SAVE',
                        f'운영평가 저장 - {control_code}',
                        '/operation/api/save', request.remote_addr,
                        request.headers.get('User-Agent'),
                        {'rcm_id': rcm_id, 'control_code': control_code})

        return jsonify({
            'success': True,
            'message': '운영평가가 저장되었습니다.'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'저장 중 오류가 발생했습니다: {str(e)}'
        }), 500


# Helper functions
def get_design_sessions(rcm_id):
    """설계평가 세션 목록 조회 (운영평가 기반)"""
    with get_db() as conn:
        sessions = conn.execute('''
            SELECT DISTINCT evaluation_session as session_name,
                   start_date as created_date,
                   evaluation_status
            FROM sb_design_evaluation_header
            WHERE rcm_id = ? AND evaluation_status = 'COMPLETED'
            ORDER BY start_date DESC
        ''', (rcm_id,)).fetchall()

        return [dict(session) for session in sessions]


def save_operation_evaluation_data(rcm_id, control_code, user_id, design_session, evaluation_data):
    """운영평가 데이터 저장"""
    with get_db() as conn:
        # 설계평가 헤더 ID 조회
        design_header = conn.execute('''
            SELECT header_id FROM sb_design_evaluation_header
            WHERE rcm_id = ? AND evaluation_session = ?
        ''', (rcm_id, design_session)).fetchone()

        if not design_header:
            raise ValueError('설계평가 세션을 찾을 수 없습니다.')

        design_header_id = design_header['header_id']

        # 운영평가 헤더 조회 또는 생성
        operation_header = conn.execute('''
            SELECT header_id FROM sb_operation_evaluation_header
            WHERE design_header_id = ? AND user_id = ?
        ''', (design_header_id, user_id)).fetchone()

        if not operation_header:
            # 헤더 생성
            cursor = conn.execute('''
                INSERT INTO sb_operation_evaluation_header
                (rcm_id, design_header_id, user_id, evaluation_status)
                VALUES (?, ?, ?, 'IN_PROGRESS')
            ''', (rcm_id, design_header_id, user_id))
            operation_header_id = cursor.lastrowid
        else:
            operation_header_id = operation_header['header_id']

        # 라인 데이터 저장
        existing = conn.execute('''
            SELECT line_id FROM sb_operation_evaluation_line
            WHERE header_id = ? AND control_code = ?
        ''', (operation_header_id, control_code)).fetchone()

        if existing:
            # 업데이트
            conn.execute('''
                UPDATE sb_operation_evaluation_line
                SET sample_size = ?,
                    exception_count = ?,
                    test_result = ?,
                    test_procedure = ?,
                    findings = ?,
                    evaluation_date = CURRENT_TIMESTAMP,
                    last_updated = CURRENT_TIMESTAMP
                WHERE line_id = ?
            ''', (
                evaluation_data.get('sample_size'),
                evaluation_data.get('exception_count'),
                evaluation_data.get('test_result'),
                evaluation_data.get('test_procedure'),
                evaluation_data.get('findings'),
                existing['line_id']
            ))
        else:
            # 신규 삽입
            conn.execute('''
                INSERT INTO sb_operation_evaluation_line
                (header_id, control_code, sample_size, exception_count,
                 test_result, test_procedure, findings, evaluation_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                operation_header_id, control_code,
                evaluation_data.get('sample_size'),
                evaluation_data.get('exception_count'),
                evaluation_data.get('test_result'),
                evaluation_data.get('test_procedure'),
                evaluation_data.get('findings')
            ))

        conn.commit()
