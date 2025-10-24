"""
Tests for RCM upload functionality
"""
import pytest
import io
from catcher_auth import get_db


class TestRCMUploadAccess:
    """Test RCM upload page access control"""

    def test_upload_page_requires_login(self, client):
        """Test that upload page requires login"""
        response = client.get('/rcm/upload')
        # Should redirect to login
        assert response.status_code == 302
        assert '/login' in response.location

    def test_upload_page_requires_admin(self, authenticated_client):
        """Test that upload page requires admin permission"""
        response = authenticated_client.get('/rcm/upload')
        # Should redirect (non-admin user)
        assert response.status_code == 302

    def test_upload_page_admin_access(self, admin_client):
        """Test that admin can access upload page"""
        response = admin_client.get('/rcm/upload')
        assert response.status_code == 200
        assert 'RCM 업로드' in response.data.decode('utf-8')


class TestIndividualUpload:
    """Test individual RCM upload (single category)"""

    def test_individual_upload_itgc(self, admin_client, sample_excel_file, admin_user, test_user):
        """Test uploading ITGC RCM individually"""
        with open(sample_excel_file, 'rb') as f:
            data = {
                'rcm_name': 'Test ITGC RCM',
                'upload_mode': 'individual',
                'control_category': 'ITGC',
                'description': 'Test ITGC upload',
                'target_user_id': str(test_user['user_id']),
                'excel_file': (f, 'test_itgc.xlsx')
            }

            response = admin_client.post(
                '/rcm/process_upload',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is True
        assert 'rcm_id' in json_data
        assert json_data['controls_count'] > 0

    def test_individual_upload_elc(self, admin_client, sample_excel_file, admin_user, test_user):
        """Test uploading ELC RCM individually"""
        with open(sample_excel_file, 'rb') as f:
            data = {
                'rcm_name': 'Test ELC RCM',
                'upload_mode': 'individual',
                'control_category': 'ELC',
                'description': 'Test ELC upload',
                'target_user_id': str(test_user['user_id']),
                'excel_file': (f, 'test_elc.xlsx')
            }

            response = admin_client.post(
                '/rcm/process_upload',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is True

    def test_individual_upload_tlc(self, admin_client, sample_excel_file, admin_user, test_user):
        """Test uploading TLC RCM individually"""
        with open(sample_excel_file, 'rb') as f:
            data = {
                'rcm_name': 'Test TLC RCM',
                'upload_mode': 'individual',
                'control_category': 'TLC',
                'description': 'Test TLC upload',
                'target_user_id': str(test_user['user_id']),
                'excel_file': (f, 'test_tlc.xlsx')
            }

            response = admin_client.post(
                '/rcm/process_upload',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is True

    def test_individual_upload_missing_category(self, admin_client, sample_excel_file, test_user):
        """Test individual upload fails without category"""
        with open(sample_excel_file, 'rb') as f:
            data = {
                'rcm_name': 'Test RCM',
                'upload_mode': 'individual',
                'description': 'Test upload',
                'target_user_id': str(test_user['user_id']),
                'excel_file': (f, 'test.xlsx')
            }

            response = admin_client.post(
                '/rcm/process_upload',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is False
        assert '카테고리' in json_data['message']


class TestIntegratedUpload:
    """Test integrated RCM upload (multiple categories)"""

    def test_integrated_upload_creates_multiple_rcms(self, admin_client, sample_integrated_excel_file, admin_user, test_user):
        """Test integrated upload creates RCMs for each category"""
        with open(sample_integrated_excel_file, 'rb') as f:
            data = {
                'rcm_name': '2024년 통합 RCM',
                'upload_mode': 'integrated',
                'description': 'Test integrated upload',
                'target_user_id': str(test_user['user_id']),
                'excel_file': (f, 'test_integrated.xlsx')
            }

            response = admin_client.post(
                '/rcm/process_upload',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is True
        assert 'rcm_ids' in json_data

        # Should create RCMs for ELC, TLC, ITGC
        rcm_ids = json_data['rcm_ids']
        assert 'ELC' in rcm_ids
        assert 'TLC' in rcm_ids
        assert 'ITGC' in rcm_ids

    def test_integrated_upload_correct_naming(self, app, admin_client, sample_integrated_excel_file, test_user):
        """Test integrated upload creates correctly named RCMs"""
        with open(sample_integrated_excel_file, 'rb') as f:
            data = {
                'rcm_name': '2024년 재무보고',
                'upload_mode': 'integrated',
                'description': 'Test naming',
                'target_user_id': str(test_user['user_id']),
                'excel_file': (f, 'test_integrated.xlsx')
            }

            response = admin_client.post(
                '/rcm/process_upload',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is True

        # Check RCM names in database
        with app.app_context():
            with get_db() as conn:
                rcms = conn.execute(
                    'SELECT rcm_name, control_category FROM sb_rcm WHERE rcm_name LIKE ?',
                    ('2024년 재무보고%',)
                ).fetchall()

                rcm_dict = {rcm['control_category']: rcm['rcm_name'] for rcm in rcms}

                assert 'ELC' in rcm_dict
                assert 'TLC' in rcm_dict
                assert 'ITGC' in rcm_dict

                assert '2024년 재무보고 - ELC' == rcm_dict['ELC']
                assert '2024년 재무보고 - TLC' == rcm_dict['TLC']
                assert '2024년 재무보고 - ITGC' == rcm_dict['ITGC']

    def test_integrated_upload_correct_data_distribution(self, app, admin_client, sample_integrated_excel_file, test_user):
        """Test integrated upload distributes controls to correct RCMs"""
        with open(sample_integrated_excel_file, 'rb') as f:
            data = {
                'rcm_name': 'Data Distribution Test',
                'upload_mode': 'integrated',
                'description': 'Test data distribution',
                'target_user_id': str(test_user['user_id']),
                'excel_file': (f, 'test_integrated.xlsx')
            }

            response = admin_client.post(
                '/rcm/process_upload',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        json_data = response.get_json()
        rcm_ids = json_data['rcm_ids']

        # Check control distribution
        with app.app_context():
            with get_db() as conn:
                # ELC should have 2 controls
                elc_controls = conn.execute(
                    'SELECT * FROM sb_rcm_detail WHERE rcm_id = ?',
                    (rcm_ids['ELC'],)
                ).fetchall()
                assert len(elc_controls) == 2

                # TLC should have 2 controls
                tlc_controls = conn.execute(
                    'SELECT * FROM sb_rcm_detail WHERE rcm_id = ?',
                    (rcm_ids['TLC'],)
                ).fetchall()
                assert len(tlc_controls) == 2

                # ITGC should have 2 controls
                itgc_controls = conn.execute(
                    'SELECT * FROM sb_rcm_detail WHERE rcm_id = ?',
                    (rcm_ids['ITGC'],)
                ).fetchall()
                assert len(itgc_controls) == 2

    def test_integrated_upload_missing_category_column(self, admin_client, sample_excel_file, test_user):
        """Test integrated upload fails without category column"""
        # sample_excel_file doesn't have category column
        with open(sample_excel_file, 'rb') as f:
            data = {
                'rcm_name': 'Test RCM',
                'upload_mode': 'integrated',
                'description': 'Should fail',
                'target_user_id': str(test_user['user_id']),
                'excel_file': (f, 'test.xlsx')
            }

            response = admin_client.post(
                '/rcm/process_upload',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is False
        assert '카테고리' in json_data['message'] or 'category' in json_data['message']


class TestUploadValidation:
    """Test upload input validation"""

    def test_upload_missing_rcm_name(self, admin_client, sample_excel_file, test_user):
        """Test upload fails without RCM name"""
        with open(sample_excel_file, 'rb') as f:
            data = {
                'upload_mode': 'individual',
                'control_category': 'ITGC',
                'target_user_id': str(test_user['user_id']),
                'excel_file': (f, 'test.xlsx')
            }

            response = admin_client.post(
                '/rcm/process_upload',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is False
        assert 'RCM명' in json_data['message']

    def test_upload_missing_target_user(self, admin_client, sample_excel_file):
        """Test upload fails without target user"""
        with open(sample_excel_file, 'rb') as f:
            data = {
                'rcm_name': 'Test RCM',
                'upload_mode': 'individual',
                'control_category': 'ITGC',
                'excel_file': (f, 'test.xlsx')
            }

            response = admin_client.post(
                '/rcm/process_upload',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is False
        assert '사용자' in json_data['message']

    def test_upload_missing_file(self, admin_client, test_user):
        """Test upload fails without Excel file"""
        data = {
            'rcm_name': 'Test RCM',
            'upload_mode': 'individual',
            'control_category': 'ITGC',
            'target_user_id': str(test_user['user_id'])
        }

        response = admin_client.post(
            '/rcm/process_upload',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is False
        assert 'Excel' in json_data['message']

    def test_upload_invalid_file_type(self, admin_client, test_user):
        """Test upload fails with non-Excel file"""
        # Create a text file
        data = {
            'rcm_name': 'Test RCM',
            'upload_mode': 'individual',
            'control_category': 'ITGC',
            'target_user_id': str(test_user['user_id']),
            'excel_file': (io.BytesIO(b"not an excel file"), 'test.txt')
        }

        response = admin_client.post(
            '/rcm/process_upload',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is False
        assert 'Excel' in json_data['message']


class TestAutoMapping:
    """Test automatic column mapping"""

    def test_auto_mapping_control_code(self):
        """Test auto mapping recognizes control code column"""
        from rcm.routes import perform_auto_mapping

        headers = ['통제코드', '통제명', '통제설명']
        mapping = perform_auto_mapping(headers)

        assert 'control_code' in mapping
        assert mapping['control_code'] == 0  # First column

    def test_auto_mapping_english_headers(self):
        """Test auto mapping works with English headers"""
        from rcm.routes import perform_auto_mapping

        headers = ['control code', 'control name', 'description']
        mapping = perform_auto_mapping(headers)

        assert 'control_code' in mapping
        assert 'control_name' in mapping
        assert 'control_description' in mapping

    def test_auto_mapping_mixed_headers(self):
        """Test auto mapping works with mixed Korean/English headers"""
        from rcm.routes import perform_auto_mapping

        headers = ['통제코드', 'control name', '설명', 'frequency']
        mapping = perform_auto_mapping(headers)

        assert 'control_code' in mapping
        assert 'control_name' in mapping
        assert 'control_description' in mapping
        assert 'control_frequency' in mapping


class TestCategoryColumn:
    """Test category column detection"""

    def test_find_category_column_korean(self):
        """Test finding category column in Korean"""
        from rcm.routes import find_category_column

        headers = ['카테고리', '통제코드', '통제명']
        idx = find_category_column(headers)

        assert idx == 0

    def test_find_category_column_english(self):
        """Test finding category column in English"""
        from rcm.routes import find_category_column

        headers = ['control code', 'category', 'control name']
        idx = find_category_column(headers)

        assert idx == 1

    def test_find_category_column_not_found(self):
        """Test when category column doesn't exist"""
        from rcm.routes import find_category_column

        headers = ['통제코드', '통제명', '설명']
        idx = find_category_column(headers)

        assert idx is None


class TestUserPermissions:
    """Test user permissions after upload"""

    def test_target_user_gets_read_permission(self, app, admin_client, sample_excel_file, test_user):
        """Test target user receives READ permission after upload"""
        with open(sample_excel_file, 'rb') as f:
            data = {
                'rcm_name': 'Permission Test RCM',
                'upload_mode': 'individual',
                'control_category': 'ITGC',
                'description': 'Test permissions',
                'target_user_id': str(test_user['user_id']),
                'excel_file': (f, 'test.xlsx')
            }

            response = admin_client.post(
                '/rcm/process_upload',
                data=data,
                content_type='multipart/form-data'
            )

        json_data = response.get_json()
        rcm_id = json_data['rcm_id']

        # Check permission in database
        with app.app_context():
            with get_db() as conn:
                permission = conn.execute(
                    'SELECT * FROM sb_user_rcm WHERE user_id = ? AND rcm_id = ?',
                    (test_user['user_id'], rcm_id)
                ).fetchone()

                assert permission is not None
                assert permission['permission_type'] == 'READ'
                assert permission['is_active'] == 'Y'
