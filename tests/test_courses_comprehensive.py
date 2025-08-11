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

"""Comprehensive tests for Course functionality."""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from now_lms.db import (
    Curso,
    CursoSeccion,
    CursoRecurso,
    CursoRecursoAvance,
    EstudianteCurso,
    DocenteCurso,
    Categoria,
    Etiqueta,
    Usuario,
    Certificacion,
    Certificado,
    database,
)


class TestCourseBasicFunctionality:
    """Test basic course model and creation."""

    def test_course_model_exists(self, app_context):
        """Test that Course model can be imported and instantiated."""
        course = Curso(
            codigo="TEST001",
            nombre="Test Course",
            descripcion_corta="Short description for test course",
            descripcion="Test course description",
            descripcion_corta="Short description",
            estado="draft",
            modalidad="self_paced",
            pagado=False,
            certificado=False,
        )
        assert course is not None
        assert course.codigo == "TEST001"
        assert course.nombre == "Test Course"

    def test_course_creation_with_database(self, app_context):
        """Test course creation and persistence in database."""
        course = Curso(
            codigo="TEST002",
            nombre="Database Test Course",
            descripcion="Testing database persistence",
            descripcion_corta="Short description",
            descripcion_corta="Testing database persistence",
            estado="draft",
            modalidad="time_based",
            pagado=True,
            precio=Decimal("99.99"
        ),
            certificado=True,
        )
        
        database.session.add(course)
        database.session.commit()
        
        # Retrieve and verify
        retrieved = database.session.execute(
            database.select(Curso).filter_by(codigo="TEST002")
        ).scalar_one()
        
        assert retrieved.nombre == "Database Test Course"
        assert retrieved.precio == Decimal("99.99")
        assert retrieved.pagado is True
        assert retrieved.certificado is True

    def test_course_modalidad_validation(self, app_context):
        """Test course modalidad (modality) options."""
        # Test self_paced
        self_paced = Curso(
            codigo="SP001",
            nombre="Self Paced Course",
            descripcion="Self paced learning",
            descripcion_corta="Short description",
            descripcion_corta="Self paced learning",
            estado="open",
            modalidad="self_paced",
        )
        assert self_paced.is_self_paced() is True
        assert self_paced.puede_habilitar_foro() is False
        
        # Test time_based
        time_based = Curso(
            codigo="TB001",
            nombre="Time Based Course",
            descripcion="Time based learning",
            descripcion_corta="Short description",
            descripcion_corta="Time based learning",
            estado="open",
            modalidad="time_based",
        )
        assert time_based.is_self_paced() is False
        assert time_based.puede_habilitar_foro() is True

    def test_course_forum_validation(self, app_context):
        """Test forum validation for different modalidades."""
        # Self-paced course cannot have forum enabled
        self_paced = Curso(
            codigo="SP002",
            modalidad="self_paced",
            foro_habilitado=False,
        )
        
        # This should be valid
        is_valid, message = self_paced.validar_foro_habilitado()
        assert is_valid is True
        
        # Try to enable forum - should fail
        self_paced.foro_habilitado = True
        is_valid, message = self_paced.validar_foro_habilitado()
        assert is_valid is False
        assert "self-paced" in message

        # Time-based course can have forum enabled
        time_based = Curso(
            codigo="TB002",
            modalidad="time_based",
            foro_habilitado=True,
        )
        is_valid, message = time_based.validar_foro_habilitado()
        assert is_valid is True


class TestCourseStructureManagement:
    """Test course sections and resources management."""

    def test_course_section_creation(self, app_context):
        """Test creation of course sections."""
        # Create a course first
        course = Curso(
            codigo="STRUCT001",
            nombre="Structured Course",
            descripcion="Course with sections",
            descripcion_corta="Short description",
            descripcion_corta="Course with sections",
            estado="draft",
        )
        database.session.add(course)
        database.session.commit()
        
        # Create sections
        section1 = CursoSeccion(
            curso="STRUCT001",
            nombre="Introduction",
            descripcion="Course introduction section",
            descripcion_corta="Short description",
            indice=1,
            estado=True,
        )
        
        section2 = CursoSeccion(
            curso="STRUCT001",
            nombre="Advanced Topics",
            descripcion="Advanced course content",
            descripcion_corta="Short description",
            indice=2,
            estado=True,
        )
        
        database.session.add_all([section1, section2])
        database.session.commit()
        
        # Verify sections
        sections = database.session.execute(
            database.select(CursoSeccion).filter_by(curso="STRUCT001").order_by(CursoSeccion.indice)
        ).scalars().all()
        
        assert len(sections) == 2
        assert sections[0].nombre == "Introduction"
        assert sections[1].nombre == "Advanced Topics"
        assert sections[0].indice == 1
        assert sections[1].indice == 2

    def test_course_resource_creation(self, app_context):
        """Test creation of course resources within sections."""
        # Create course and section
        course = Curso(
            codigo="RES001", nombre="Resource Course", estado="draft"
        )
        database.session.add(course)
        database.session.commit()
        
        section = CursoSeccion(
            curso="RES001",
            nombre="Video Section",
            descripcion="Section with video resources",
            descripcion_corta="Short description",
            indice=1,
        )
        database.session.add(section)
        database.session.commit()
        
        # Create resources
        video_resource = CursoRecurso(
            seccion=section.id,
            curso="RES001",
            nombre="Introduction Video",
            descripcion="Course introduction video",
            descripcion_corta="Short description",
            tipo="youtube",
            url="https://youtube.com/watch?v=example",
            indice=1,
            requerido="required",
            publico=True,
        )
        
        pdf_resource = CursoRecurso(
            seccion=section.id,
            curso="RES001",
            nombre="Course Materials",
            descripcion="Downloadable course materials",
            descripcion_corta="Short description",
            tipo="pdf",
            indice=2,
            requerido="optional",
            publico=True,
        )
        
        database.session.add_all([video_resource, pdf_resource])
        database.session.commit()
        
        # Verify resources
        resources = database.session.execute(
            database.select(CursoRecurso).filter_by(curso="RES001").order_by(CursoRecurso.indice)
        ).scalars().all()
        
        assert len(resources) == 2
        assert resources[0].tipo == "youtube"
        assert resources[1].tipo == "pdf"
        assert resources[0].requerido == "required"
        assert resources[1].requerido == "optional"


class TestCourseEnrollmentAndProgress:
    """Test student enrollment and progress tracking."""

    def test_student_enrollment(self, app_context):
        """Test student enrollment in courses."""
        # Create course
        course = Curso(
            codigo="ENROLL001",
            nombre="Enrollment Test Course",
            estado="open",
            publico=True,
        )
        database.session.add(course)
        
        # Create student
        student = Usuario(
            usuario="student_enroll",
            acceso=b"password123",
            nombre="Test",
            apellido="Student",
            correo_electronico="student@test.com",
            tipo="user",
            
        )
        database.session.add(student)
        database.session.commit()
        
        # Enroll student
        enrollment = EstudianteCurso(
            curso="ENROLL001",
            usuario="student_enroll",
        )
        database.session.add(enrollment)
        database.session.commit()
        
        # Verify enrollment
        enrolled = database.session.execute(
            database.select(EstudianteCurso).filter_by(curso="ENROLL001", usuario="student_enroll")
        ).scalar_one()
        
        assert enrolled is not None
        assert enrolled.curso == "ENROLL001"
        assert enrolled.usuario == "student_enroll"

    def test_resource_progress_tracking(self, app_context):
        """Test tracking student progress on course resources."""
        # Create course structure
        course = Curso(
            codigo="PROG001", nombre="Progress Course", estado="open"
        )
        database.session.add(course)
        database.session.commit()
        
        section = CursoSeccion(curso="PROG001", nombre="Progress Section", indice=1)
        database.session.add(section)
        database.session.commit()
        
        resource = CursoRecurso(
            seccion=section.id,
            curso="PROG001",
            nombre="Progress Resource",
            tipo="text",
            indice=1,
            requerido="required",
        )
        database.session.add(resource)
        
        # Create student
        student = Usuario(
            usuario="progress_student",
            acceso=b"pass123",
            nombre="Progress",
            apellido="Student",
            correo_electronico="progress@test.com",
            tipo="user",
        )
        database.session.add(student)
        database.session.commit()
        
        # Track progress
        progress = CursoRecursoAvance(
            curso="PROG001",
            recurso=resource.id,
            usuario="progress_student",
        )
        database.session.add(progress)
        database.session.commit()
        
        # Verify progress tracking
        tracked_progress = database.session.execute(
            database.select(CursoRecursoAvance).filter_by(
                curso="PROG001",
                usuario="progress_student"
            )
        ).scalar_one()
        
        assert tracked_progress is not None
        assert tracked_progress.recurso == resource.id

    def test_instructor_assignment(self, app_context):
        """Test instructor assignment to courses."""
        # Create course
        course = Curso(
            codigo="INSTR001", nombre="Instructor Course", estado="draft"
        )
        database.session.add(course)
        
        # Create instructor
        instructor = Usuario(
            usuario="course_instructor",
            acceso=b"instrpass123",
            nombre="Course",
            apellido="Instructor",
            correo_electronico="instructor@test.com",
            tipo="instructor",
            
        )
        database.session.add(instructor)
        database.session.commit()
        
        # Assign instructor
        assignment = DocenteCurso(
            curso="INSTR001",
            usuario="course_instructor",
        )
        database.session.add(assignment)
        database.session.commit()
        
        # Verify assignment
        assigned = database.session.execute(
            database.select(DocenteCurso).filter_by(curso="INSTR001")
        ).scalar_one()
        
        assert assigned.usuario == "course_instructor"


class TestCourseCertificationSystem:
    """Test course completion and certificate generation."""

    def test_course_certificate_configuration(self, app_context):
        """Test course certificate configuration."""
        # Create certificate template first
        cert_template = Certificado(
            code="CERT_TEMPLATE",
            title="Course Certificate",
            habilitado=True,
            publico=True,
        )
        database.session.add(cert_template)
        database.session.commit()
        
        # Create course with certificate
        course = Curso(
            codigo="CERT001",
            nombre="Certificate Course",
            descripcion="Course that awards certificates",
            descripcion_corta="Short description",
            descripcion_corta="Course that awards certificates",
            estado="open",
            certificado=True,
            plantilla_certificado="CERT_TEMPLATE",
        )
        database.session.add(course)
        database.session.commit()
        
        # Verify certificate configuration
        retrieved_course = database.session.execute(
            database.select(Curso).filter_by(codigo="CERT001")
        ).scalar_one()
        
        assert retrieved_course.certificado is True
        assert retrieved_course.plantilla_certificado == "CERT_TEMPLATE"

    def test_certificate_generation_for_course(self, app_context):
        """Test certificate generation when course is completed."""
        # Create course with certificate
        course = Curso(
            codigo="CERTGEN001",
            nombre="Certificate Generation Course",
            estado="open",
            certificado=True,
        )
        database.session.add(course)
        
        # Create certificate template
        cert_template = Certificado(
            code="GEN_TEMPLATE",
            title="Generated Certificate",
            habilitado=True,
        )
        database.session.add(cert_template)
        
        # Create student
        student = Usuario(
            usuario="cert_student",
            acceso=b"certpass123",
            nombre="Certificate",
            apellido="Student",
            correo_electronico="cert@test.com",
            tipo="user",
        )
        database.session.add(student)
        database.session.commit()
        
        # Generate certificate
        certification = Certificacion(
            usuario="cert_student",
            curso="CERTGEN001",
            certificado="GEN_TEMPLATE",
            fecha=date.today(),
            nota=Decimal("95.5"),
        )
        database.session.add(certification)
        database.session.commit()
        
        # Verify certificate
        generated_cert = database.session.execute(
            database.select(Certificacion).filter_by(usuario="cert_student", curso="CERTGEN001")
        ).scalar_one()
        
        assert generated_cert is not None
        assert generated_cert.nota == Decimal("95.5")
        assert generated_cert.get_content_type() == "course"
        
        # Test get_content_info method
        content_info = generated_cert.get_content_info()
        assert content_info is not None
        assert content_info.codigo == "CERTGEN001"


class TestCoursePaymentSystem:
    """Test course payment and access control."""

    def test_paid_course_configuration(self, app_context):
        """Test paid course setup and pricing."""
        paid_course = Curso(
            codigo="PAID001",
            nombre="Premium Course",
            descripcion="This is a paid course",
            descripcion_corta="Short description",
            descripcion_corta="This is a paid course",
            estado="open",
            pagado=True,
            precio=Decimal("199.99"
        ),
            publico=True,
        )
        database.session.add(paid_course)
        database.session.commit()
        
        # Verify paid course configuration
        retrieved = database.session.execute(
            database.select(Curso).filter_by(codigo="PAID001")
        ).scalar_one()
        
        assert retrieved.pagado is True
        assert retrieved.precio == Decimal("199.99")

    def test_free_course_configuration(self, app_context):
        """Test free course setup."""
        free_course = Curso(
            codigo="FREE001",
            nombre="Free Course",
            descripcion="This is a free course",
            descripcion_corta="Short description",
            descripcion_corta="This is a free course",
            estado="open",
            pagado=False,
            precio=None,
            publico=True,
        )
        database.session.add(free_course)
        database.session.commit()
        
        # Verify free course configuration
        retrieved = database.session.execute(
            database.select(Curso).filter_by(codigo="FREE001")
        ).scalar_one()
        
        assert retrieved.pagado is False
        assert retrieved.precio is None

    def test_course_capacity_limits(self, app_context):
        """Test course capacity and enrollment limits."""
        limited_course = Curso(
            codigo="LIMITED001",
            nombre="Limited Capacity Course",
            descripcion="Course with enrollment limits",
            descripcion_corta="Short description",
            descripcion_corta="Course with enrollment limits",
            estado="open",
            limitado=True,
            capacidad=5,
        )
        database.session.add(limited_course)
        database.session.commit()
        
        # Verify capacity configuration
        retrieved = database.session.execute(
            database.select(Curso).filter_by(codigo="LIMITED001")
        ).scalar_one()
        
        assert retrieved.limitado is True
        assert retrieved.capacidad == 5


class TestCourseSchedulingAndDates:
    """Test course scheduling and date management."""

    def test_course_with_start_end_dates(self, app_context):
        """Test course scheduling with start and end dates."""
        start_date = date.today() + timedelta(days=7)
        end_date = date.today() + timedelta(days=37)
        
        scheduled_course = Curso(
            codigo="SCHED001",
            nombre="Scheduled Course",
            descripcion="Course with specific dates",
            descripcion_corta="Short description",
            descripcion_corta="Course with specific dates",
            estado="open",
            modalidad="time_based",
            fecha_inicio=start_date,
            fecha_fin=end_date,
        )
        database.session.add(scheduled_course)
        database.session.commit()
        
        # Verify scheduling
        retrieved = database.session.execute(
            database.select(Curso).filter_by(codigo="SCHED001")
        ).scalar_one()
        
        assert retrieved.fecha_inicio == start_date
        assert retrieved.fecha_fin == end_date

    def test_self_paced_course_no_dates(self, app_context):
        """Test self-paced course without specific dates."""
        self_paced = Curso(
            codigo="SELFP001",
            nombre="Self Paced Course",
            descripcion="Learn at your own pace",
            descripcion_corta="Short description",
            descripcion_corta="Learn at your own pace",
            estado="open",
            modalidad="self_paced",
            fecha_inicio=None,
            fecha_fin=None,
        )
        database.session.add(self_paced)
        database.session.commit()
        
        # Verify no dates set
        retrieved = database.session.execute(
            database.select(Curso).filter_by(codigo="SELFP001")
        ).scalar_one()
        
        assert retrieved.fecha_inicio is None
        assert retrieved.fecha_fin is None
        assert retrieved.is_self_paced() is True


class TestCourseStateManagement:
    """Test course state transitions and visibility."""

    def test_course_draft_state(self, app_context):
        """Test course in draft state."""
        draft_course = Curso(
            codigo="DRAFT001",
            nombre="Draft Course",
            descripcion="Course under development",
            descripcion_corta="Short description",
            descripcion_corta="Course under development",
            estado="draft",
            publico=False,
        )
        database.session.add(draft_course)
        database.session.commit()
        
        # Verify draft state
        retrieved = database.session.execute(
            database.select(Curso).filter_by(codigo="DRAFT001")
        ).scalar_one()
        
        assert retrieved.estado == "draft"
        assert retrieved.publico is False

    def test_course_open_state(self, app_context):
        """Test course in open state."""
        open_course = Curso(
            codigo="OPEN001",
            nombre="Open Course",
            descripcion="Course accepting enrollments",
            descripcion_corta="Short description",
            descripcion_corta="Course accepting enrollments",
            estado="open",
            publico=True,
        )
        database.session.add(open_course)
        database.session.commit()
        
        # Verify open state
        retrieved = database.session.execute(
            database.select(Curso).filter_by(codigo="OPEN001")
        ).scalar_one()
        
        assert retrieved.estado == "open"
        assert retrieved.publico is True

    def test_course_closed_state(self, app_context):
        """Test course in closed state."""
        closed_course = Curso(
            codigo="CLOSED001",
            nombre="Closed Course",
            descripcion="Course no longer accepting enrollments",
            descripcion_corta="Short description",
            descripcion_corta="Course no longer accepting enrollments",
            estado="closed",
            publico=True,
        )
        database.session.add(closed_course)
        database.session.commit()
        
        # Verify closed state
        retrieved = database.session.execute(
            database.select(Curso).filter_by(codigo="CLOSED001")
        ).scalar_one()
        
        assert retrieved.estado == "closed"

    def test_course_finalized_state(self, app_context):
        """Test course in finalized state."""
        finalized_course = Curso(
            codigo="FINAL001",
            nombre="Finalized Course",
            descripcion="Completed course",
            descripcion_corta="Short description",
            descripcion_corta="Completed course",
            estado="finalized",
            publico=True,
        )
        database.session.add(finalized_course)
        database.session.commit()
        
        # Verify finalized state
        retrieved = database.session.execute(
            database.select(Curso).filter_by(codigo="FINAL001")
        ).scalar_one()
        
        assert retrieved.estado == "finalized"


class TestCourseCategorizationAndTagging:
    """Test course categories and tags."""

    def test_course_categorization(self, app_context):
        """Test assigning categories to courses."""
        # Create category
        category = Categoria(
            
            nombre="Technology",
            descripcion="Technology related courses",
            descripcion_corta="Short description",
            
        )
        database.session.add(category)
        database.session.commit()
        
        # Create course with category
        course = Curso(
            codigo="CAT001",
            nombre="Tech Course",
            descripcion="Technology course",
            descripcion_corta="Short description",
            descripcion_corta="Technology course",
            estado="open",
        )
        database.session.add(course)
        database.session.commit()
        
        # Note: The actual category assignment would be done through
        # CategoriaCurso relationship table in a real implementation
        
        # Verify category exists
        retrieved_category = database.session.execute(
            database.select(Categoria).filter_by(codigo="TECH")
        ).scalar_one()
        
        assert retrieved_category.nombre == "Technology"

    def test_course_tagging(self, app_context):
        """Test assigning tags to courses."""
        # Create tag
        tag = Etiqueta(
            
            nombre="Python Programming",
            descripcion="Python related content",
            descripcion_corta="Short description",
            
        )
        database.session.add(tag)
        database.session.commit()
        
        # Create course
        course = Curso(
            codigo="TAG001",
            nombre="Python Course",
            descripcion="Learn Python programming",
            descripcion_corta="Short description",
            descripcion_corta="Learn Python programming",
            estado="open",
        )
        database.session.add(course)
        database.session.commit()
        
        # Note: The actual tag assignment would be done through
        # EtiquetaCurso relationship table in a real implementation
        
        # Verify tag exists
        retrieved_tag = database.session.execute(
            database.select(Etiqueta).filter_by(codigo="PYTHON")
        ).scalar_one()
        
        assert retrieved_tag.nombre == "Python Programming"


class TestCourseValidationAndConstraints:
    """Test course validation rules and database constraints."""

    def test_course_codigo_uniqueness(self, app_context):
        """Test that course codes must be unique."""
        course1 = Curso(
            codigo="UNIQUE001",
            nombre="First Course",
            descripcion="First course with this code",
            descripcion_corta="Short description",
            descripcion_corta="First course with this code",
            estado="draft",
        )
        database.session.add(course1)
        database.session.commit()
        
        # Try to create another course with same code
        course2 = Curso(
            codigo="UNIQUE001",
            nombre="Second Course",
            descripcion="Second course with same code",
            descripcion_corta="Short description",
            descripcion_corta="Second course with same code",
            estado="draft",
        )
        database.session.add(course2)
        
        # Should raise integrity error
        with pytest.raises(Exception):
            database.session.commit()

    def test_course_required_fields(self, app_context):
        """Test that required fields are enforced."""
        # Course without codigo should fail
        with pytest.raises(Exception):
            course = Curso(
            nombre="No Code Course",
            descripcion="Course without code",
            descripcion_corta="Short description",
            descripcion_corta="Course without code",
            estado="draft",
        )
            database.session.add(course)
            database.session.commit()

    def test_forum_validation_on_save(self, app_context):
        """Test forum validation when saving to database."""
        # This should work fine
        valid_course = Curso(
            codigo="VALID_FORUM",
            modalidad="time_based",
            foro_habilitado=True,
        )
        database.session.add(valid_course)
        database.session.commit()
        
        # This should raise validation error
        with pytest.raises(ValueError):
            invalid_course = Curso(
            codigo="INVALID_FORUM",
            modalidad="self_paced",
            foro_habilitado=True,
        )
            database.session.add(invalid_course)
            database.session.commit()