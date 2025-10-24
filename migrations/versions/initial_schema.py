"""
Initial Database Schema for Sentinel
내부회계관리제도(ICFR) 통합 관리 시스템
"""

import sqlite3
from datetime import datetime

def upgrade(conn):
    """데이터베이스 스키마 생성"""

    # 사용자 테이블 생성
    conn.execute('''
        CREATE TABLE IF NOT EXISTS st_user (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            user_email TEXT UNIQUE NOT NULL,
            user_password TEXT NOT NULL,
            company_name TEXT NOT NULL,
            department TEXT,
            admin_flag TEXT DEFAULT 'N',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            effective_end_date TIMESTAMP DEFAULT NULL,
            last_login TIMESTAMP
        )
    ''')

    # 사용자 활동 로그 테이블
    conn.execute('''
        CREATE TABLE IF NOT EXISTS st_user_activity (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            activity_description TEXT,
            activity_url TEXT,
            ip_address TEXT,
            user_agent TEXT,
            additional_info TEXT,
            activity_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES st_user (user_id)
        )
    ''')

    # RCM 마스터 테이블 생성 (ELC/TLC/ITGC 구분 추가)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS st_rcm (
            rcm_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rcm_name TEXT NOT NULL,
            control_category TEXT NOT NULL CHECK(control_category IN ('ELC', 'TLC', 'ITGC')),
            description TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            upload_user_id INTEGER NOT NULL,
            is_active TEXT DEFAULT 'Y',
            completion_date TIMESTAMP DEFAULT NULL,
            original_filename TEXT,
            company_name TEXT,
            FOREIGN KEY (upload_user_id) REFERENCES st_user (user_id)
        )
    ''')

    # RCM 상세 데이터 테이블 생성
    conn.execute('''
        CREATE TABLE IF NOT EXISTS st_rcm_detail (
            detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rcm_id INTEGER NOT NULL,
            control_code TEXT NOT NULL,
            control_name TEXT NOT NULL,
            control_description TEXT,
            key_control TEXT,
            control_frequency TEXT,
            control_type TEXT,
            control_nature TEXT,
            process_area TEXT,
            risk_description TEXT,
            risk_impact TEXT,
            risk_likelihood TEXT,
            population TEXT,
            population_completeness_check TEXT,
            population_count TEXT,
            test_procedure TEXT,
            control_owner TEXT,
            control_performer TEXT,
            evidence_type TEXT,
            mapped_std_control_id INTEGER,
            mapped_date TIMESTAMP,
            mapped_by INTEGER,
            ai_review_status TEXT DEFAULT 'not_reviewed',
            ai_review_recommendation TEXT,
            ai_reviewed_date TIMESTAMP,
            ai_reviewed_by INTEGER,
            mapping_status TEXT,
            FOREIGN KEY (rcm_id) REFERENCES st_rcm (rcm_id),
            FOREIGN KEY (mapped_by) REFERENCES st_user (user_id),
            FOREIGN KEY (ai_reviewed_by) REFERENCES st_user (user_id),
            UNIQUE(rcm_id, control_code)
        )
    ''')

    # 사용자-RCM 매핑 테이블 생성
    conn.execute('''
        CREATE TABLE IF NOT EXISTS st_user_rcm (
            mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            rcm_id INTEGER NOT NULL,
            permission_type TEXT DEFAULT 'READ',
            granted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            granted_by INTEGER,
            is_active TEXT DEFAULT 'Y',
            FOREIGN KEY (user_id) REFERENCES st_user (user_id),
            FOREIGN KEY (rcm_id) REFERENCES st_rcm (rcm_id),
            FOREIGN KEY (granted_by) REFERENCES st_user (user_id),
            UNIQUE(user_id, rcm_id)
        )
    ''')

    # 설계평가 헤더 테이블
    conn.execute('''
        CREATE TABLE IF NOT EXISTS st_design_evaluation_header (
            header_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rcm_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            evaluation_session TEXT NOT NULL,
            evaluation_status TEXT DEFAULT 'IN_PROGRESS',
            total_controls INTEGER DEFAULT 0,
            evaluated_controls INTEGER DEFAULT 0,
            progress_percentage REAL DEFAULT 0.0,
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completion_date TIMESTAMP DEFAULT NULL,
            FOREIGN KEY (rcm_id) REFERENCES st_rcm (rcm_id),
            FOREIGN KEY (user_id) REFERENCES st_user (user_id),
            UNIQUE(rcm_id, evaluation_session)
        )
    ''')

    # 설계평가 상세 테이블
    conn.execute('''
        CREATE TABLE IF NOT EXISTS st_design_evaluation (
            eval_id INTEGER PRIMARY KEY AUTOINCREMENT,
            header_id INTEGER NOT NULL,
            detail_id INTEGER NOT NULL,
            control_code TEXT NOT NULL,
            design_effectiveness TEXT,
            design_comments TEXT,
            design_deficiency TEXT,
            design_recommendation TEXT,
            evaluator_name TEXT,
            evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (header_id) REFERENCES st_design_evaluation_header (header_id),
            FOREIGN KEY (detail_id) REFERENCES st_rcm_detail (detail_id),
            UNIQUE(header_id, detail_id)
        )
    ''')

    # 운영평가 헤더 테이블
    conn.execute('''
        CREATE TABLE IF NOT EXISTS st_operation_evaluation_header (
            header_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rcm_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            evaluation_session TEXT NOT NULL,
            evaluation_status TEXT DEFAULT 'IN_PROGRESS',
            total_controls INTEGER DEFAULT 0,
            evaluated_controls INTEGER DEFAULT 0,
            progress_percentage REAL DEFAULT 0.0,
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completion_date TIMESTAMP DEFAULT NULL,
            FOREIGN KEY (rcm_id) REFERENCES st_rcm (rcm_id),
            FOREIGN KEY (user_id) REFERENCES st_user (user_id),
            UNIQUE(rcm_id, evaluation_session)
        )
    ''')

    # 운영평가 상세 테이블
    conn.execute('''
        CREATE TABLE IF NOT EXISTS st_operation_evaluation (
            eval_id INTEGER PRIMARY KEY AUTOINCREMENT,
            header_id INTEGER NOT NULL,
            detail_id INTEGER NOT NULL,
            control_code TEXT NOT NULL,
            sample_size INTEGER,
            sample_selection_method TEXT,
            test_result TEXT,
            exceptions_found INTEGER DEFAULT 0,
            exception_details TEXT,
            operation_effectiveness TEXT,
            operation_comments TEXT,
            evaluator_name TEXT,
            evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            population_file_path TEXT,
            sample_file_path TEXT,
            evidence_file_paths TEXT,
            FOREIGN KEY (header_id) REFERENCES st_operation_evaluation_header (header_id),
            FOREIGN KEY (detail_id) REFERENCES st_rcm_detail (detail_id),
            UNIQUE(header_id, detail_id)
        )
    ''')

    # RCM 업로드 세션 테이블 (Excel 매핑용)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS st_rcm_upload_session (
            session_id TEXT PRIMARY KEY,
            rcm_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            original_filename TEXT,
            excel_headers TEXT,
            column_mapping TEXT,
            sample_data TEXT,
            upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'PENDING',
            FOREIGN KEY (rcm_id) REFERENCES st_rcm (rcm_id),
            FOREIGN KEY (user_id) REFERENCES st_user (user_id)
        )
    ''')

    conn.commit()
    print("✓ Sentinel 데이터베이스 스키마 생성 완료")

def downgrade(conn):
    """데이터베이스 스키마 삭제"""
    tables = [
        'st_operation_evaluation',
        'st_operation_evaluation_header',
        'st_design_evaluation',
        'st_design_evaluation_header',
        'st_rcm_upload_session',
        'st_user_rcm',
        'st_rcm_detail',
        'st_rcm',
        'st_user_activity',
        'st_user'
    ]

    for table in tables:
        conn.execute(f'DROP TABLE IF EXISTS {table}')

    conn.commit()
    print("✓ Sentinel 데이터베이스 스키마 삭제 완료")

if __name__ == '__main__':
    # 테스트용
    db_path = '/Users/newsistraphael/Pythons/sentinel/sentinel.db'
    conn = sqlite3.connect(db_path)
    upgrade(conn)
    conn.close()
