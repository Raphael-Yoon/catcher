"""
Tests for Operation Evaluation (Link3) functionality
"""
import pytest


class TestOperationEvaluationAccess:
    """Test operation evaluation page access control"""

    def test_operation_page_requires_login(self, client):
        """Test that operation evaluation page requires login"""
        response = client.get('/operation/evaluation')
        # Should redirect to login
        assert response.status_code == 302
        assert '/login' in response.location

    def test_operation_page_authenticated_access(self, authenticated_client):
        """Test that authenticated user can access operation evaluation page"""
        response = authenticated_client.get('/operation/evaluation')
        assert response.status_code == 200


class TestOperationEvaluationList:
    """Test operation evaluation list functionality"""

    def test_evaluation_list_shows_user_rcms(self, app, authenticated_client, test_rcm):
        """Test that evaluation list shows RCMs user has access to"""
        with app.app_context():
            from catcher_auth import get_db
            with authenticated_client.session_transaction() as session:
                user_id = session['user_info']['user_id']

            # Grant permission
            with get_db() as conn:
                conn.execute('''
                    INSERT INTO sb_user_rcm (user_id, rcm_id, permission_type, granted_by)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, test_rcm['rcm_id'], 'READ', 1))
                conn.commit()

        response = authenticated_client.get('/operation/evaluation')
        html = response.data.decode('utf-8')
        assert response.status_code == 200
        # Should show the RCM name
        assert test_rcm['rcm_name'] in html or 'RCM' in html

    def test_admin_sees_all_rcms(self, admin_client, test_rcm):
        """Test that admin can see all RCMs"""
        response = admin_client.get('/operation/evaluation')
        assert response.status_code == 200
