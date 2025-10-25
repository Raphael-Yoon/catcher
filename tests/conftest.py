"""
pytest configuration and shared fixtures for Catcher
"""
import pytest
import os
import sys
import tempfile
import shutil
from datetime import datetime

# Add parent directory to path to import catcher modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import catcher
# Import fix for catcher module
import importlib.util
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
spec = importlib.util.spec_from_file_location("catcher_main", os.path.join(parent_dir, "catcher.py"))
catcher_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catcher_main)
flask_app = catcher_main.app
from catcher_auth import get_db


@pytest.fixture
def app():
    """Create and configure a test Flask application instance."""
    # Set test configuration
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test_secret_key_catcher',
        'SESSION_COOKIE_SECURE': False,
        'WTF_CSRF_ENABLED': False,
    })

    # Create a temporary database for testing
    # Copy the existing catcher.db as template
    original_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'catcher.db')
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    if os.path.exists(original_db):
        shutil.copy(original_db, db_path)
    else:
        # Create basic test tables if no DB exists
        _create_basic_test_tables(db_path)

    # Override DB path
    os.environ['CATCHER_DB_PATH'] = db_path

    yield flask_app

    # Cleanup
    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)


def _create_basic_test_tables(db_path):
    """Create basic test tables if database doesn't exist"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create essential tables for testing (based on snowball schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ca_user (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT UNIQUE NOT NULL,
            user_name TEXT NOT NULL,
            company_name TEXT,
            user_password TEXT,
            admin_flag TEXT DEFAULT 'N',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            effective_end_date TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ca_rcm (
            rcm_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rcm_name TEXT NOT NULL,
            control_category TEXT NOT NULL,
            description TEXT,
            upload_user_id INTEGER,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completion_date TIMESTAMP,
            original_filename TEXT,
            is_active TEXT DEFAULT 'Y',
            FOREIGN KEY (upload_user_id) REFERENCES ca_user(user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ca_rcm_detail (
            detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rcm_id INTEGER NOT NULL,
            control_code TEXT NOT NULL,
            control_name TEXT,
            control_description TEXT,
            key_control TEXT,
            control_frequency TEXT,
            control_type TEXT,
            control_nature TEXT,
            population TEXT,
            population_completeness_check TEXT,
            population_count TEXT,
            test_procedure TEXT,
            FOREIGN KEY (rcm_id) REFERENCES ca_rcm(rcm_id),
            UNIQUE(rcm_id, control_code)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ca_user_rcm (
            mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            rcm_id INTEGER NOT NULL,
            permission_type TEXT DEFAULT 'READ',
            granted_by INTEGER,
            granted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active TEXT DEFAULT 'Y',
            FOREIGN KEY (user_id) REFERENCES ca_user(user_id),
            FOREIGN KEY (rcm_id) REFERENCES ca_rcm(rcm_id),
            UNIQUE(user_id, rcm_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ca_user_activity_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_email TEXT,
            user_name TEXT,
            action_type TEXT,
            page_name TEXT,
            url_path TEXT,
            ip_address TEXT,
            user_agent TEXT,
            additional_info TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a test user in the database."""
    with app.app_context():
        with get_db() as conn:
            # Check if user already exists
            existing = conn.execute(
                'SELECT * FROM ca_user WHERE user_email = ?',
                ('test@catcher.com',)
            ).fetchone()

            if existing:
                return dict(existing)

            # Create new user
            cursor = conn.execute('''
                INSERT INTO ca_user (user_email, user_name, company_name, admin_flag)
                VALUES (?, ?, ?, ?)
            ''', ('test@catcher.com', 'Test User', 'Test Company', 'N'))
            user_id = cursor.lastrowid
            conn.commit()

            return {
                'user_id': user_id,
                'user_email': 'test@catcher.com',
                'user_name': 'Test User',
                'company_name': 'Test Company',
                'admin_flag': 'N'
            }


@pytest.fixture
def admin_user(app):
    """Create an admin user in the database."""
    with app.app_context():
        with get_db() as conn:
            # Check if user already exists
            existing = conn.execute(
                'SELECT * FROM ca_user WHERE user_email = ?',
                ('admin@catcher.com',)
            ).fetchone()

            if existing:
                return dict(existing)

            # Create new admin user
            cursor = conn.execute('''
                INSERT INTO ca_user (user_email, user_name, company_name, admin_flag)
                VALUES (?, ?, ?, ?)
            ''', ('admin@catcher.com', 'Admin User', 'Catcher Corp', 'Y'))
            user_id = cursor.lastrowid
            conn.commit()

            return {
                'user_id': user_id,
                'user_email': 'admin@catcher.com',
                'user_name': 'Admin User',
                'company_name': 'Catcher Corp',
                'admin_flag': 'Y'
            }


@pytest.fixture
def authenticated_client(client, test_user):
    """Create an authenticated test client with a logged-in user."""
    with client.session_transaction() as session:
        session['user_id'] = test_user['user_id']
        session['user_email'] = test_user['user_email']
        session['user_info'] = test_user
        session['last_activity'] = datetime.now().isoformat()

    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Create an authenticated admin test client."""
    with client.session_transaction() as session:
        session['user_id'] = admin_user['user_id']
        session['user_email'] = admin_user['user_email']
        session['user_info'] = admin_user
        session['last_activity'] = datetime.now().isoformat()

    return client


@pytest.fixture
def test_rcm(app, admin_user):
    """Create a test RCM in the database."""
    with app.app_context():
        from catcher_auth import create_rcm

        rcm_id = create_rcm(
            rcm_name='Test RCM - ITGC',
            control_category='ITGC',
            description='Test RCM for automated testing',
            upload_user_id=admin_user['user_id'],
            original_filename='test_rcm.xlsx'
        )

        return {
            'rcm_id': rcm_id,
            'rcm_name': 'Test RCM - ITGC',
            'control_category': 'ITGC',
            'description': 'Test RCM for automated testing',
            'upload_user_id': admin_user['user_id']
        }


@pytest.fixture
def sample_excel_file():
    """Create a sample Excel file for testing upload."""
    from openpyxl import Workbook
    import tempfile

    wb = Workbook()
    ws = wb.active
    ws.title = 'RCM'

    # Add headers
    headers = ['통제코드', '통제명', '통제설명', '핵심통제여부', '통제빈도', '통제유형']
    ws.append(headers)

    # Add sample data
    ws.append(['ITGC-001', '시스템 접근 통제', '시스템 접근 권한 관리', 'Y', '연간', '예방'])
    ws.append(['ITGC-002', '변경 관리', '시스템 변경 승인 및 이행', 'Y', '수시', '예방'])
    ws.append(['ITGC-003', '백업 관리', '데이터 백업 및 복구', 'N', '일일', '적발'])

    # Save to temporary file
    fd, path = tempfile.mkstemp(suffix='.xlsx')
    wb.save(path)
    os.close(fd)

    yield path

    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def sample_integrated_excel_file():
    """Create a sample integrated Excel file with category column."""
    from openpyxl import Workbook
    import tempfile

    wb = Workbook()
    ws = wb.active
    ws.title = 'RCM'

    # Add headers including category
    headers = ['카테고리', '통제코드', '통제명', '통제설명', '핵심통제여부']
    ws.append(headers)

    # Add sample data for different categories
    ws.append(['ELC', 'ELC-001', '이사회 운영', '정기 이사회 개최', 'Y'])
    ws.append(['ELC', 'ELC-002', '내부감사', '내부감사 수행', 'Y'])
    ws.append(['TLC', 'TLC-001', '매출 승인', '매출 거래 승인 절차', 'Y'])
    ws.append(['TLC', 'TLC-002', '구매 승인', '구매 거래 승인 절차', 'Y'])
    ws.append(['ITGC', 'ITGC-001', '시스템 접근 통제', '시스템 접근 권한 관리', 'Y'])
    ws.append(['ITGC', 'ITGC-002', '변경 관리', '시스템 변경 승인', 'Y'])

    # Save to temporary file
    fd, path = tempfile.mkstemp(suffix='.xlsx')
    wb.save(path)
    os.close(fd)

    yield path

    # Cleanup
    if os.path.exists(path):
        os.unlink(path)
