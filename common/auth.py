"""
Sentinel Authentication and Authorization Module
Snowball 데이터베이스 스키마 사용
"""

import sqlite3
import os
from functools import wraps
from flask import session, redirect, url_for, g, request
from datetime import datetime
import hashlib

# 데이터베이스 경로
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sentinel.db')

def get_db():
    """데이터베이스 연결 반환"""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """데이터베이스 연결 닫기"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def hash_password(password):
    """비밀번호 해싱"""
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    """로그인 필요한 페이지에 대한 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_info' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """관리자 권한 필요한 페이지에 대한 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_info' not in session:
            return redirect(url_for('login'))
        user_info = session['user_info']
        if user_info.get('admin_flag') != 'Y':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """현재 로그인한 사용자 정보 반환"""
    if 'user_info' in session:
        return session['user_info']
    return None

def authenticate_user(email, password):
    """사용자 인증"""
    db = get_db()
    hashed_password = hash_password(password)
    user = db.execute('''
        SELECT user_id, user_name, user_email, company_name, department, admin_flag
        FROM sb_user
        WHERE user_email = ? AND user_password = ?
        AND (effective_end_date IS NULL OR effective_end_date > CURRENT_TIMESTAMP)
    ''', (email, hashed_password)).fetchone()

    if user:
        # 마지막 로그인 시간 업데이트
        db.execute('UPDATE sb_user SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?',
                  (user['user_id'],))
        db.commit()
        return dict(user)
    return None

def create_user(user_name, user_email, password, company_name, department='', admin_flag='N'):
    """사용자 생성"""
    db = get_db()
    hashed_password = hash_password(password)

    try:
        cursor = db.execute('''
            INSERT INTO sb_user (user_name, user_email, user_password, company_name, department, admin_flag)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_name, user_email, hashed_password, company_name, department, admin_flag))
        db.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None  # 이미 존재하는 이메일

def create_rcm(rcm_name, control_category, description, upload_user_id, original_filename=None):
    """RCM 생성 (ELC/TLC/ITGC 구분)"""
    db = get_db()
    cursor = db.execute('''
        INSERT INTO sb_rcm (rcm_name, control_category, description, upload_user_id, original_filename)
        VALUES (?, ?, ?, ?, ?)
    ''', (rcm_name, control_category, description, upload_user_id, original_filename))
    db.commit()
    return cursor.lastrowid

def get_user_rcms(user_id, control_category=None):
    """사용자가 접근 가능한 RCM 목록 조회 (카테고리 필터 옵션)"""
    db = get_db()

    # 먼저 사용자가 관리자인지 확인
    user = db.execute('SELECT admin_flag FROM sb_user WHERE user_id = ?', (user_id,)).fetchone()
    is_admin = user and user['admin_flag'] == 'Y'

    if is_admin:
        # 관리자는 모든 RCM에 접근 가능
        if control_category:
            rcms = db.execute('''
                SELECT r.rcm_id, r.rcm_name, r.control_category, r.description, r.upload_date,
                       r.completion_date, 'admin' as permission_type, u.company_name
                FROM sb_rcm r
                INNER JOIN sb_user u ON r.upload_user_id = u.user_id
                WHERE r.is_active = 'Y' AND r.control_category = ?
                ORDER BY r.control_category, r.upload_date DESC
            ''', (control_category,)).fetchall()
        else:
            rcms = db.execute('''
                SELECT r.rcm_id, r.rcm_name, r.control_category, r.description, r.upload_date,
                       r.completion_date, 'admin' as permission_type, u.company_name
                FROM sb_rcm r
                INNER JOIN sb_user u ON r.upload_user_id = u.user_id
                WHERE r.is_active = 'Y'
                ORDER BY r.control_category, r.upload_date DESC
            ''').fetchall()
    else:
        # 일반 사용자는 권한이 있는 RCM만 접근 가능
        if control_category:
            rcms = db.execute('''
                SELECT r.rcm_id, r.rcm_name, r.control_category, r.description, r.upload_date,
                       r.completion_date, ur.permission_type, u.company_name
                FROM sb_rcm r
                INNER JOIN sb_user_rcm ur ON r.rcm_id = ur.rcm_id
                INNER JOIN sb_user u ON r.upload_user_id = u.user_id
                WHERE ur.user_id = ? AND ur.is_active = 'Y' AND r.is_active = 'Y'
                AND r.control_category = ?
                ORDER BY r.control_category, r.upload_date DESC
            ''', (user_id, control_category)).fetchall()
        else:
            rcms = db.execute('''
                SELECT r.rcm_id, r.rcm_name, r.control_category, r.description, r.upload_date,
                       r.completion_date, ur.permission_type, u.company_name
                FROM sb_rcm r
                INNER JOIN sb_user_rcm ur ON r.rcm_id = ur.rcm_id
                INNER JOIN sb_user u ON r.upload_user_id = u.user_id
                WHERE ur.user_id = ? AND ur.is_active = 'Y' AND r.is_active = 'Y'
                ORDER BY r.control_category, r.upload_date DESC
            ''', (user_id,)).fetchall()

    return [dict(rcm) for rcm in rcms]

def has_rcm_access(user_id, rcm_id):
    """사용자가 특정 RCM에 접근 권한이 있는지 확인"""
    db = get_db()

    # 먼저 관리자인지 확인
    user = db.execute('SELECT admin_flag FROM sb_user WHERE user_id = ?', (user_id,)).fetchone()
    if user and user['admin_flag'] == 'Y':
        return True

    # 일반 사용자는 명시적 권한 확인
    access = db.execute('''
        SELECT mapping_id FROM sb_user_rcm
        WHERE user_id = ? AND rcm_id = ? AND is_active = 'Y'
    ''', (user_id, rcm_id)).fetchone()

    return access is not None

def grant_rcm_access(user_id, rcm_id, granted_by, permission_type='READ'):
    """사용자에게 RCM 접근 권한 부여"""
    db = get_db()
    try:
        db.execute('''
            INSERT INTO sb_user_rcm (user_id, rcm_id, permission_type, granted_by)
            VALUES (?, ?, ?, ?)
        ''', (user_id, rcm_id, permission_type, granted_by))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        # 이미 권한이 있는 경우 업데이트
        db.execute('''
            UPDATE sb_user_rcm
            SET permission_type = ?, is_active = 'Y', granted_date = CURRENT_TIMESTAMP, granted_by = ?
            WHERE user_id = ? AND rcm_id = ?
        ''', (permission_type, granted_by, user_id, rcm_id))
        db.commit()
        return True

def get_rcm_details(rcm_id):
    """RCM 상세 데이터 조회"""
    db = get_db()
    details = db.execute('''
        SELECT * FROM sb_rcm_detail
        WHERE rcm_id = ?
        ORDER BY control_code
    ''', (rcm_id,)).fetchall()
    return [dict(detail) for detail in details]

def get_rcm_info(rcm_id):
    """RCM 기본 정보 조회"""
    db = get_db()
    rcm = db.execute('''
        SELECT r.*, u.user_name as uploader_name, u.company_name
        FROM sb_rcm r
        LEFT JOIN sb_user u ON r.upload_user_id = u.user_id
        WHERE r.rcm_id = ?
    ''', (rcm_id,)).fetchone()
    return dict(rcm) if rcm else None

def save_rcm_details(rcm_id, controls_data):
    """RCM 상세 데이터 저장 (Excel 업로드 후)"""
    db = get_db()

    for control in controls_data:
        try:
            db.execute('''
                INSERT INTO sb_rcm_detail (
                    rcm_id, control_code, control_name, control_description,
                    key_control, control_frequency, control_type, control_nature,
                    population, population_completeness_check, population_count,
                    test_procedure
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rcm_id,
                control.get('control_code'),
                control.get('control_name'),
                control.get('control_description'),
                control.get('key_control'),
                control.get('control_frequency'),
                control.get('control_type'),
                control.get('control_nature'),
                control.get('population'),
                control.get('population_completeness_check'),
                control.get('population_count'),
                control.get('test_procedure')
            ))
        except sqlite3.IntegrityError:
            # 중복된 control_code는 업데이트
            db.execute('''
                UPDATE sb_rcm_detail SET
                    control_name = ?, control_description = ?,
                    key_control = ?, control_frequency = ?, control_type = ?, control_nature = ?,
                    population = ?, population_completeness_check = ?, population_count = ?,
                    test_procedure = ?
                WHERE rcm_id = ? AND control_code = ?
            ''', (
                control.get('control_name'),
                control.get('control_description'),
                control.get('key_control'),
                control.get('control_frequency'),
                control.get('control_type'),
                control.get('control_nature'),
                control.get('population'),
                control.get('population_completeness_check'),
                control.get('population_count'),
                control.get('test_procedure'),
                rcm_id,
                control.get('control_code')
            ))

    db.commit()

def log_user_activity(user_info, activity_type, description, url, ip_address, user_agent, additional_info=None):
    """사용자 활동 로그 기록"""
    if not user_info:
        return

    db = get_db()
    db.execute('''
        INSERT INTO sb_user_activity_log (
            user_id, user_email, user_name, action_type, page_name, url_path,
            ip_address, user_agent, additional_info
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_info['user_id'],
        user_info.get('user_email', ''),
        user_info.get('user_name', ''),
        activity_type,
        description,
        url,
        ip_address,
        user_agent,
        str(additional_info) if additional_info else None
    ))
    db.commit()
