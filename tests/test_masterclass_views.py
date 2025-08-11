# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Test Master Class views and functionality."""

import pytest
from datetime import datetime, date, time, timedelta
from unittest.mock import patch, MagicMock

from now_lms.db import MasterClass, MasterClassEnrollment, Usuario, database


class TestMasterClassViews:
    """Test master class views."""

    def setup_method(self):
        """Set up test data for each test."""
        # Create instructor user
        self.instructor = Usuario(
            usuario="instructor_test",
            acceso=b"test_password",
            nombre="Juan",
            apellido="Instructor",
            correo_electronico="instructor@test.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(self.instructor)

        # Create student user
        self.student = Usuario(
            usuario="student_test",
            acceso=b"test_password",
            nombre="Ana",
            apellido="Estudiante",
            correo_electronico="student@test.com",
            tipo="user",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(self.student)

        # Create admin user
        self.admin = Usuario(
            usuario="admin_test",
            acceso=b"test_password",
            nombre="Admin",
            apellido="User",
            correo_electronico="admin@test.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(self.admin)

        database.session.commit()

        # Create test master classes
        future_date = date.today() + timedelta(days=7)
        past_date = date.today() - timedelta(days=7)

        self.future_masterclass = MasterClass(
            title="Future Master Class",
            slug="future-master-class",
            description_public="A future master class",
            description_private="Private details",
            date=future_date,
            start_time=time(14, 0),
            end_time=time(16, 0),
            is_paid=False,
            platform_name="Zoom",
            platform_url="https://zoom.us/j/test",
            instructor_id=self.instructor.usuario,
        )
        database.session.add(self.future_masterclass)

        self.past_masterclass = MasterClass(
            title="Past Master Class",
            slug="past-master-class",
            description_public="A past master class",
            date=past_date,
            start_time=time(10, 0),
            end_time=time(12, 0),
            is_paid=False,
            platform_name="Google Meet",
            platform_url="https://meet.google.com/test",
            instructor_id=self.instructor.usuario,
        )
        database.session.add(self.past_masterclass)

        database.session.commit()

    def test_list_public_master_classes(self, client, full_db_setup):
        """Test public listing of master classes."""
        response = client.get('/masterclass/')
        assert response.status_code == 200
        assert b"Future Master Class" in response.data
        # Past classes should not appear in public listing
        assert b"Past Master Class" not in response.data

    def test_list_public_master_classes_with_pagination(self, client, full_db_setup):
        """Test public listing with pagination."""
        response = client.get('/masterclass/?page=1')
        assert response.status_code == 200

    def test_detail_public_master_class(self, client, full_db_setup):
        """Test public detail view of master class."""
        response = client.get('/masterclass/future-master-class')
        assert response.status_code == 200
        assert b"Future Master Class" in response.data
        assert b"A future master class" in response.data

    def test_detail_public_master_class_not_found(self, client, full_db_setup):
        """Test public detail view for non-existent master class."""
        response = client.get('/masterclass/non-existent-slug')
        assert response.status_code == 404

    @patch('now_lms.vistas.masterclass.current_user')
    def test_detail_public_master_class_with_enrollment_check(self, mock_current_user, client, full_db_setup):
        """Test public detail view shows enrollment status for authenticated users."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.student.usuario

        response = client.get('/masterclass/future-master-class')
        assert response.status_code == 200

    def test_enroll_unauthenticated(self, client, full_db_setup):
        """Test enrollment redirect for unauthenticated users."""
        response = client.get('/masterclass/future-master-class/enroll')
        assert response.status_code == 302  # Redirect to login

    @patch('now_lms.vistas.masterclass.current_user')
    def test_enroll_get_form(self, mock_current_user, client, full_db_setup):
        """Test getting enrollment form."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.student.usuario

        response = client.get('/masterclass/future-master-class/enroll')
        assert response.status_code == 200
        assert b"enroll" in response.data.lower()

    @patch('now_lms.vistas.masterclass.current_user')
    def test_enroll_post_success(self, mock_current_user, client, full_db_setup):
        """Test successful enrollment."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.student.usuario

        response = client.post('/masterclass/future-master-class/enroll', data={
            'csrf_token': 'test_token'  # Assuming CSRF is disabled in tests
        }, follow_redirects=True)
        assert response.status_code == 200

        # Check enrollment was created
        enrollment = database.session.execute(
            database.select(MasterClassEnrollment)
            .filter_by(master_class_id=self.future_masterclass.id, user_id=self.student.usuario)
        ).scalar_one_or_none()
        assert enrollment is not None
        assert enrollment.is_confirmed is True

    @patch('now_lms.vistas.masterclass.current_user')
    def test_enroll_already_enrolled(self, mock_current_user, client, full_db_setup):
        """Test enrollment when already enrolled."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.student.usuario

        # Create existing enrollment
        enrollment = MasterClassEnrollment(
            master_class_id=self.future_masterclass.id,
            user_id=self.student.usuario,
            is_confirmed=True
        )
        database.session.add(enrollment)
        database.session.commit()

        response = client.get('/masterclass/future-master-class/enroll')
        assert response.status_code == 302  # Redirect back to detail

    @patch('now_lms.vistas.masterclass.current_user')
    def test_enroll_non_existent_class(self, mock_current_user, client, full_db_setup):
        """Test enrollment for non-existent master class."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.student.usuario

        response = client.get('/masterclass/non-existent/enroll')
        assert response.status_code == 404

    def test_instructor_list_unauthenticated(self, client, full_db_setup):
        """Test instructor list redirects unauthenticated users."""
        response = client.get('/masterclass/instructor')
        assert response.status_code == 302  # Redirect to login

    @patch('now_lms.vistas.masterclass.current_user')
    def test_instructor_list_unauthorized(self, mock_current_user, client, full_db_setup):
        """Test instructor list denies access to non-instructors."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.student.usuario
        mock_current_user.tipo = "user"

        response = client.get('/masterclass/instructor')
        assert response.status_code == 403

    @patch('now_lms.vistas.masterclass.current_user')
    def test_instructor_list_authorized(self, mock_current_user, client, full_db_setup):
        """Test instructor list for authorized users."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.instructor.usuario
        mock_current_user.tipo = "instructor"

        response = client.get('/masterclass/instructor')
        assert response.status_code == 200

    def test_instructor_create_unauthenticated(self, client, full_db_setup):
        """Test instructor create redirects unauthenticated users."""
        response = client.get('/masterclass/instructor/create')
        assert response.status_code == 302  # Redirect to login

    @patch('now_lms.vistas.masterclass.current_user')
    def test_instructor_create_unauthorized(self, mock_current_user, client, full_db_setup):
        """Test instructor create denies access to non-instructors."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.student.usuario
        mock_current_user.tipo = "user"

        response = client.get('/masterclass/instructor/create')
        assert response.status_code == 403

    @patch('now_lms.vistas.masterclass.current_user')
    def test_instructor_create_get_form(self, mock_current_user, client, full_db_setup):
        """Test getting instructor create form."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.instructor.usuario
        mock_current_user.tipo = "instructor"

        response = client.get('/masterclass/instructor/create')
        assert response.status_code == 200

    @patch('now_lms.vistas.masterclass.current_user')
    def test_instructor_create_with_duplicate_slug(self, mock_current_user, client, full_db_setup):
        """Test creation handles duplicate slugs properly."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.instructor.usuario
        mock_current_user.tipo = "instructor"

        future_date = date.today() + timedelta(days=30)
        
        # Try to create a master class with the same title (will generate same slug)
        response = client.post('/masterclass/instructor/create', data={
            'title': 'Future Master Class',  # Same as existing
            'description_public': 'New description',
            'date': future_date.isoformat(),
            'start_time': '15:00',
            'end_time': '17:00',
            'platform_name': 'Teams',
            'platform_url': 'https://teams.microsoft.com/test',
            'csrf_token': 'test_token'
        }, follow_redirects=True)
        
        # Should still succeed with modified slug
        assert response.status_code == 200

    def test_instructor_edit_unauthenticated(self, client, full_db_setup):
        """Test instructor edit redirects unauthenticated users."""
        response = client.get(f'/masterclass/instructor/{self.future_masterclass.id}/edit')
        assert response.status_code == 302  # Redirect to login

    @patch('now_lms.vistas.masterclass.current_user')
    def test_instructor_edit_unauthorized(self, mock_current_user, client, full_db_setup):
        """Test instructor edit denies access to non-instructors."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.student.usuario
        mock_current_user.tipo = "user"

        response = client.get(f'/masterclass/instructor/{self.future_masterclass.id}/edit')
        assert response.status_code == 403

    @patch('now_lms.vistas.masterclass.current_user')
    def test_instructor_edit_not_owner(self, mock_current_user, client, full_db_setup):
        """Test instructor edit denies access to non-owners."""
        # Create another instructor
        other_instructor = Usuario(
            usuario="other_instructor",
            acceso=b"test_password",
            nombre="Other",
            apellido="Instructor",
            correo_electronico="other@test.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(other_instructor)
        database.session.commit()

        mock_current_user.is_authenticated = True
        mock_current_user.usuario = other_instructor.usuario
        mock_current_user.tipo = "instructor"

        response = client.get(f'/masterclass/instructor/{self.future_masterclass.id}/edit')
        assert response.status_code == 403

    @patch('now_lms.vistas.masterclass.current_user')
    def test_instructor_edit_admin_access(self, mock_current_user, client, full_db_setup):
        """Test admin can edit any master class."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.admin.usuario
        mock_current_user.tipo = "admin"

        response = client.get(f'/masterclass/instructor/{self.future_masterclass.id}/edit')
        assert response.status_code == 200

    @patch('now_lms.vistas.masterclass.current_user')
    def test_instructor_edit_non_existent(self, mock_current_user, client, full_db_setup):
        """Test instructor edit for non-existent master class."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.instructor.usuario
        mock_current_user.tipo = "instructor"

        response = client.get('/masterclass/instructor/999999/edit')
        assert response.status_code == 404

    def test_instructor_students_unauthenticated(self, client, full_db_setup):
        """Test instructor students view redirects unauthenticated users."""
        response = client.get(f'/masterclass/instructor/{self.future_masterclass.id}/students')
        assert response.status_code == 302  # Redirect to login

    @patch('now_lms.vistas.masterclass.current_user')
    def test_instructor_students_unauthorized(self, mock_current_user, client, full_db_setup):
        """Test instructor students view denies access to non-instructors."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.student.usuario
        mock_current_user.tipo = "user"

        response = client.get(f'/masterclass/instructor/{self.future_masterclass.id}/students')
        assert response.status_code == 403

    @patch('now_lms.vistas.masterclass.current_user')
    def test_instructor_students_authorized(self, mock_current_user, client, full_db_setup):
        """Test instructor students view for authorized users."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.instructor.usuario
        mock_current_user.tipo = "instructor"

        # Add some enrollments
        enrollment = MasterClassEnrollment(
            master_class_id=self.future_masterclass.id,
            user_id=self.student.usuario,
            is_confirmed=True
        )
        database.session.add(enrollment)
        database.session.commit()

        response = client.get(f'/masterclass/instructor/{self.future_masterclass.id}/students')
        assert response.status_code == 200

    def test_my_enrollments_unauthenticated(self, client, full_db_setup):
        """Test my enrollments redirects unauthenticated users."""
        response = client.get('/masterclass/my-enrollments')
        assert response.status_code == 302  # Redirect to login

    @patch('now_lms.vistas.masterclass.current_user')
    def test_my_enrollments_authenticated(self, mock_current_user, client, full_db_setup):
        """Test my enrollments for authenticated users."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.student.usuario

        # Add enrollment
        enrollment = MasterClassEnrollment(
            master_class_id=self.future_masterclass.id,
            user_id=self.student.usuario,
            is_confirmed=True
        )
        database.session.add(enrollment)
        database.session.commit()

        response = client.get('/masterclass/my-enrollments')
        assert response.status_code == 200

    def test_admin_list_unauthenticated(self, client, full_db_setup):
        """Test admin list redirects unauthenticated users."""
        response = client.get('/masterclass/admin')
        assert response.status_code == 302  # Redirect to login

    @patch('now_lms.vistas.masterclass.current_user')
    def test_admin_list_unauthorized(self, mock_current_user, client, full_db_setup):
        """Test admin list denies access to non-admins."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.student.usuario
        mock_current_user.tipo = "user"

        response = client.get('/masterclass/admin')
        assert response.status_code == 403

    @patch('now_lms.vistas.masterclass.current_user')
    def test_admin_list_authorized(self, mock_current_user, client, full_db_setup):
        """Test admin list for authorized admins."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.admin.usuario
        mock_current_user.tipo = "admin"

        response = client.get('/masterclass/admin')
        assert response.status_code == 200

    @patch('now_lms.vistas.masterclass.current_user')
    def test_admin_list_with_pagination(self, mock_current_user, client, full_db_setup):
        """Test admin list with pagination."""
        mock_current_user.is_authenticated = True
        mock_current_user.usuario = self.admin.usuario
        mock_current_user.tipo = "admin"

        response = client.get('/masterclass/admin?page=1')
        assert response.status_code == 200


class TestMasterClassHelpers:
    """Test master class helper functions and edge cases."""

    def setup_method(self):
        """Set up test data for each test."""
        # Create instructor user
        self.instructor = Usuario(
            usuario="instructor_test",
            acceso=b"test_password",
            nombre="Juan",
            apellido="Instructor",
            correo_electronico="instructor@test.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(self.instructor)
        database.session.commit()

    def test_master_class_slug_generation(self, full_db_setup):
        """Test automatic slug generation from title."""
        # Test that slug is generated correctly
        future_date = date.today() + timedelta(days=1)
        master_class = MasterClass(
            title="Test Class With Special Chars!@#",
            slug="test-slug",  # Will be overridden by view
            description_public="Test description",
            date=future_date,
            start_time=time(10, 0),
            end_time=time(12, 0),
            is_paid=False,
            platform_name="Zoom",
            platform_url="https://zoom.us/j/test",
            instructor_id=self.instructor.usuario,
        )
        database.session.add(master_class)
        database.session.commit()

        assert master_class.slug is not None

    def test_master_class_required_fields(self, full_db_setup):
        """Test master class with minimal required fields."""
        future_date = date.today() + timedelta(days=1)
        master_class = MasterClass(
            title="Minimal Class",
            slug="minimal-class",
            description_public="Minimal description",
            date=future_date,
            start_time=time(10, 0),
            end_time=time(12, 0),
            is_paid=False,
            instructor_id=self.instructor.usuario,
        )
        database.session.add(master_class)
        database.session.commit()

        assert master_class.id is not None
        assert master_class.is_paid is False
        assert master_class.price is None

    def test_master_class_with_certificate(self, full_db_setup):
        """Test master class with certificate option."""
        future_date = date.today() + timedelta(days=1)
        master_class = MasterClass(
            title="Certificate Class",
            slug="certificate-class",
            description_public="Class with certificate",
            date=future_date,
            start_time=time(10, 0),
            end_time=time(12, 0),
            is_paid=False,
            is_certificate=True,
            instructor_id=self.instructor.usuario,
        )
        database.session.add(master_class)
        database.session.commit()

        assert master_class.is_certificate is True

    def test_enrollment_confirmation_status(self, full_db_setup):
        """Test enrollment confirmation logic."""
        future_date = date.today() + timedelta(days=1)
        master_class = MasterClass(
            title="Test Class",
            slug="test-class",
            description_public="Test description",
            date=future_date,
            start_time=time(10, 0),
            end_time=time(12, 0),
            is_paid=False,
            instructor_id=self.instructor.usuario,
        )
        database.session.add(master_class)

        student = Usuario(
            usuario="student_test",
            acceso=b"test_password",
            nombre="Test",
            apellido="Student",
            correo_electronico="student@test.com",
            tipo="user",
            activo=True,
        )
        database.session.add(student)
        database.session.commit()

        # Test enrollment
        enrollment = MasterClassEnrollment(
            master_class_id=master_class.id,
            user_id=student.usuario,
            is_confirmed=True,  # Always confirmed for free classes
            payment_id=None
        )
        database.session.add(enrollment)
        database.session.commit()

        assert enrollment.is_confirmed is True
        assert enrollment.payment_id is None