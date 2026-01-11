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
"""
Tests for resource completion redirect functionality.

Validates that marking a resource as completed redirects to the next resource.
"""

import pytest
from flask import url_for


class TestResourceCompletionRedirect:
    """Tests for automatic redirect to next resource after completion."""

    @pytest.fixture
    def setup_course_with_resources(self, app, db_session):
        """Create a course with multiple resources for testing navigation."""
        from now_lms.db import (
            Usuario,
            Curso,
            CursoSeccion,
            CursoRecurso,
            EstudianteCurso,
            Pago,
            database,
        )
        from now_lms.auth import proteger_passwd

        with app.app_context():
            # Create an instructor
            instructor = Usuario(
                usuario="instructor1",
                nombre="Test",
                apellido="Instructor",
                correo_electronico="instructor@test.com",
                tipo="instructor",
                activo=True,
                acceso=proteger_passwd("password123"),
            )
            database.session.add(instructor)

            # Create a student
            student = Usuario(
                usuario="student1",
                nombre="Test",
                apellido="Student",
                correo_electronico="student@test.com",
                tipo="student",
                activo=True,
                acceso=proteger_passwd("password123"),
            )
            database.session.add(student)

            # Create a course
            course = Curso(
                codigo="TEST001",
                nombre="Test Course",
                descripcion_corta="Test course for navigation",
                descripcion="Test course for navigation and learning",
                publico=True,
                pagado=False,
                estado="open",
                creado_por="instructor1",
            )
            database.session.add(course)

            # Create a section
            section = CursoSeccion(
                curso="TEST001",
                nombre="Section 1",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            database.session.add(section)
            database.session.flush()

            # Create three sequential resources
            resource1 = CursoRecurso(
                curso="TEST001",
                seccion=section.id,
                tipo="youtube",
                id="RES001",
                nombre="Resource 1",
                descripcion="First resource",
                url="https://www.youtube.com/watch?v=test1",
                indice=1,
                requerido="required",
                publico=True,
            )
            database.session.add(resource1)

            resource2 = CursoRecurso(
                curso="TEST001",
                seccion=section.id,
                tipo="youtube",
                id="RES002",
                nombre="Resource 2",
                descripcion="Second resource",
                url="https://www.youtube.com/watch?v=test2",
                indice=2,
                requerido="required",
                publico=True,
            )
            database.session.add(resource2)

            resource3 = CursoRecurso(
                curso="TEST001",
                seccion=section.id,
                tipo="youtube",
                id="RES003",
                nombre="Resource 3",
                descripcion="Third resource",
                url="https://www.youtube.com/watch?v=test3",
                indice=3,
                requerido="required",
                publico=True,
            )
            database.session.add(resource3)

            # Enroll student in course
            enrollment = EstudianteCurso(
                usuario="student1",
                curso="TEST001",
            )
            database.session.add(enrollment)

            # Create payment record for enrollment
            payment = Pago(
                usuario="student1",
                curso="TEST001",
                monto=0,
                estado="completed",
                metodo="free",
                nombre="Test",
                apellido="Student",
                correo_electronico="student@test.com",
            )
            database.session.add(payment)

            database.session.commit()

            return {
                "student": student,
                "instructor": instructor,
                "course": course,
                "section": section,
                "resources": [resource1, resource2, resource3],
            }

    def test_mark_first_resource_redirects_to_second(self, app, client, setup_course_with_resources):
        """Test that marking first resource as complete redirects to second resource."""
        data = setup_course_with_resources

        with app.app_context():
            # Login as student (this establishes session)
            response = client.post(
                "/user/login",
                data={"usuario": "student1", "password": "password123"},
                follow_redirects=True,
            )
            
            # Verify login was successful (should not be on login page)
            assert response.status_code == 200

            # Mark first resource as completed
            response = client.get(
                f"/course/TEST001/resource/youtube/RES001/complete",
                follow_redirects=False,
            )

            # Should redirect (302)
            assert response.status_code == 302

            # Should redirect to second resource (RES002)
            assert "/course/TEST001/resource/youtube/RES002" in response.location

    def test_mark_middle_resource_redirects_to_next(self, app, client, setup_course_with_resources):
        """Test that marking middle resource as complete redirects to next resource."""
        data = setup_course_with_resources

        with app.app_context():
            # Login as student
            client.post(
                "/user/login",
                data={"usuario": "student1", "password": "password123"},
                follow_redirects=True,
            )

            # Mark second resource as completed
            response = client.get(
                f"/course/TEST001/resource/youtube/RES002/complete",
                follow_redirects=False,
            )

            # Should redirect (302)
            assert response.status_code == 302

            # Should redirect to third resource (RES003)
            assert "/course/TEST001/resource/youtube/RES003" in response.location

    def test_mark_last_resource_stays_on_page(self, app, client, setup_course_with_resources):
        """Test that marking last resource as complete stays on same page."""
        data = setup_course_with_resources

        with app.app_context():
            # Login as student
            client.post(
                "/user/login",
                data={"usuario": "student1", "password": "password123"},
                follow_redirects=True,
            )

            # Mark last resource as completed
            response = client.get(
                f"/course/TEST001/resource/youtube/RES003/complete",
                follow_redirects=False,
            )

            # Should redirect (302)
            assert response.status_code == 302

            # Should stay on same resource (RES003) since there's no next resource
            assert "/course/TEST001/resource/youtube/RES003" in response.location
