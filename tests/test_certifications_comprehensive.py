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

"""Comprehensive tests for Certification functionality."""

import pytest
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
from io import BytesIO

from now_lms.db import (
    Certificacion,
    Certificado,
    Curso,
    MasterClass,
    Usuario,
    database,
)


class TestCertificateTemplateManagement:
    """Test certificate template creation and management."""

    def test_certificate_template_creation(self, app_context):
        """Test basic certificate template creation."""
        template = Certificado(
            code="TEMPLATE001",
            titulo="Basic Certificate Template",
            habilitado=True,
            publico=True,
        )
        database.session.add(template)
        database.session.commit()
        
        # Verify template creation
        retrieved = database.session.execute(
            database.select(Certificado).filter_by(code="TEMPLATE001")
        ).scalar_one()
        
        assert retrieved.title == "Basic Certificate Template"
        assert retrieved.habilitado is True
        assert retrieved.publico is True

    def test_certificate_template_with_content(self, app_context):
        """Test certificate template with HTML and CSS content."""
        template = Certificado(
            code="CONTENT_TEMPLATE",
            titulo="Certificate with Content",
            html="<h1>Certificate of Completion</h1><p>{{student_name}}</p>",
            css="h1 { color: blue; } p { font-size: 14px; }",
            habilitado=True,
            publico=True,
        )
        database.session.add(template)
        database.session.commit()
        
        # Verify content
        retrieved = database.session.execute(
            database.select(Certificado).filter_by(code="CONTENT_TEMPLATE")
        ).scalar_one()
        
        assert "Certificate of Completion" in retrieved.html
        assert "{{student_name}}" in retrieved.html
        assert "color: blue" in retrieved.css

    def test_certificate_template_user_association(self, app_context):
        """Test certificate template associated with a user."""
        # Create user
        user = Usuario(
            usuario="template_creator",
            acceso=b"password123",
            nombre="Template",
            apellido="Creator",
            correo_electronico="creator@test.com",
            tipo="admin",
            activo=True,
        )
        database.session.add(user)
        database.session.commit()

        # Create template with user association
        template = Certificado(
            code="USER_TEMPLATE",
            titulo="User Created Template",
            habilitado=True,
            publico=False,
            usuario="template_creator",
        )
        database.session.add(template)
        database.session.commit()
        
        # Verify user association
        retrieved = database.session.execute(
            database.select(Certificado).filter_by(code="USER_TEMPLATE")
        ).scalar_one()
        
        assert retrieved.usuario == "template_creator"
        assert retrieved.publico is False

    def test_certificate_template_status_management(self, app_context):
        """Test certificate template enable/disable functionality."""
        # Create enabled template
        enabled_template = Certificado(
            code="ENABLED_TEMPLATE",
            titulo="Enabled Certificate",
            habilitado=True,
            publico=True,
        )
        
        # Create disabled template
        disabled_template = Certificado(
            code="DISABLED_TEMPLATE",
            titulo="Disabled Certificate",
            habilitado=False,
            publico=True,
        )
        
        database.session.add_all([enabled_template, disabled_template])
        database.session.commit()
        
        # Verify status
        enabled = database.session.execute(
            database.select(Certificado).filter_by(code="ENABLED_TEMPLATE")
        ).scalar_one()
        
        disabled = database.session.execute(
            database.select(Certificado).filter_by(code="DISABLED_TEMPLATE")
        ).scalar_one()
        
        assert enabled.habilitado is True
        assert disabled.habilitado is False


class TestCertificationForCourses:
    """Test certification generation and management for courses."""

    def test_course_certification_basic(self, app_context):
        """Test basic certification for course completion."""
        # Create certificate template
        template = Certificado(
            code="COURSE_CERT",
            titulo="Course Completion Certificate",
            habilitado=True,
        )
        database.session.add(template)
        
        # Create course
        course = Curso(
            codigo="CERT_COURSE001",
            nombre="Certification Course",
            descripcion="Course that awards certificates",
            estado="open",
            certificado=True,
            plantilla_certificado="COURSE_CERT",
        )
        database.session.add(course)
        
        # Create student
        student = Usuario(
            usuario="course_student",
            acceso=b"studentpass123",
            nombre="Course",
            apellido="Student",
            correo_electronico="student@course.com",
            tipo="user",
            activo=True,
        )
        database.session.add(student)
        database.session.commit()
        
        # Create certification
        certification = Certificacion(
            usuario="course_student",
            curso="CERT_COURSE001",
            certificado="COURSE_CERT",
            fecha=date.today(),
            nota=Decimal("88.5"),
        )
        database.session.add(certification)
        database.session.commit()
        
        # Verify certification
        retrieved = database.session.execute(
            database.select(Certificacion).filter_by(
                usuario="course_student",
                curso="CERT_COURSE001"
            )
        ).scalar_one()
        
        assert retrieved.nota == Decimal("88.5")
        assert retrieved.get_content_type() == "course"
        assert retrieved.certificado == "COURSE_CERT"

    def test_course_certification_content_info(self, app_context):
        """Test getting course information from certification."""
        # Create template and course
        template = Certificado(
            code="COURSE_INFO_CERT",
            titulo="Course Info Certificate",
            habilitado=True,
        )
        
        course = Curso(
            codigo="INFO_COURSE001",
            nombre="Information Test Course",
            descripcion="Course for testing information retrieval",
            estado="finalized",
            certificado=True,
        )
        
        student = Usuario(
            usuario="info_student",
            acceso=b"infopass123",
            nombre="Info",
            apellido="Student",
            correo_electronico="info@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([template, course, student])
        database.session.commit()
        
        # Create certification
        certification = Certificacion(
            usuario="info_student",
            curso="INFO_COURSE001",
            certificado="COURSE_INFO_CERT",
            fecha=date.today(),
        )
        database.session.add(certification)
        database.session.commit()
        
        # Test content info retrieval
        content_info = certification.get_content_info()
        assert content_info is not None
        assert content_info.nombre == "Information Test Course"
        assert content_info.codigo == "INFO_COURSE001"

    def test_course_certification_with_grade(self, app_context):
        """Test course certification with different grades."""
        # Create template and course
        template = Certificado(code="GRADE_CERT", titulo="Grade Certificate", habilitado=True)
        course = Curso(codigo="GRADE_COURSE", nombre="Graded Course", estado="open", certificado=True)
        student = Usuario(
            usuario="graded_student",
            acceso=b"gradepass123",
            nombre="Graded",
            apellido="Student",
            correo_electronico="grade@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([template, course, student])
        database.session.commit()
        
        # Test with excellent grade
        excellent_cert = Certificacion(
            usuario="graded_student",
            curso="GRADE_COURSE",
            certificado="GRADE_CERT",
            fecha=date.today(),
            nota=Decimal("95.0"),
        )
        database.session.add(excellent_cert)
        database.session.commit()
        
        # Verify excellent grade
        retrieved = database.session.execute(
            database.select(Certificacion).filter_by(
                usuario="graded_student",
                curso="GRADE_COURSE"
            )
        ).scalar_one()
        
        assert retrieved.nota == Decimal("95.0")

    def test_multiple_course_certifications(self, app_context):
        """Test student with multiple course certifications."""
        # Create templates
        template1 = Certificado(code="MULTI_CERT1", titulo="Multi Certificate 1", habilitado=True)
        template2 = Certificado(code="MULTI_CERT2", titulo="Multi Certificate 2", habilitado=True)
        
        # Create courses
        course1 = Curso(codigo="MULTI_COURSE1", nombre="Multi Course 1", estado="finalized", certificado=True)
        course2 = Curso(codigo="MULTI_COURSE2", nombre="Multi Course 2", estado="finalized", certificado=True)
        
        # Create student
        student = Usuario(
            usuario="multi_student",
            acceso=b"multipass123",
            nombre="Multi",
            apellido="Student",
            correo_electronico="multi@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([template1, template2, course1, course2, student])
        database.session.commit()
        
        # Create multiple certifications
        cert1 = Certificacion(
            usuario="multi_student",
            curso="MULTI_COURSE1",
            certificado="MULTI_CERT1",
            fecha=date.today() - timedelta(days=30),
            nota=Decimal("87.5"),
        )
        
        cert2 = Certificacion(
            usuario="multi_student",
            curso="MULTI_COURSE2",
            certificado="MULTI_CERT2",
            fecha=date.today(),
            nota=Decimal("92.0"),
        )
        
        database.session.add_all([cert1, cert2])
        database.session.commit()
        
        # Verify multiple certifications
        certifications = database.session.execute(
            database.select(Certificacion).filter_by(usuario="multi_student")
        ).scalars().all()
        
        assert len(certifications) == 2
        assert all(cert.get_content_type() == "course" for cert in certifications)


class TestCertificationForMasterClasses:
    """Test certification generation and management for MasterClasses."""

    def test_masterclass_certification_basic(self, app_context):
        """Test basic certification for MasterClass completion."""
        # Create certificate template
        template = Certificado(
            code="MC_CERT",
            titulo="MasterClass Certificate",
            habilitado=True,
        )
        database.session.add(template)
        
        # Create instructor
        instructor = Usuario(
            usuario="mc_instructor",
            acceso=b"instructorpass123",
            nombre="MasterClass",
            apellido="Instructor",
            correo_electronico="instructor@mc.com",
            tipo="instructor",
            activo=True,
        )
        
        # Create student
        student = Usuario(
            usuario="mc_student",
            acceso=b"mcstudentpass123",
            nombre="MasterClass",
            apellido="Student",
            correo_electronico="student@mc.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([instructor, student])
        database.session.commit()
        
        # Create MasterClass
        masterclass = MasterClass(
            titulo="Certification MasterClass",
            slug="cert-masterclass",
            description_public="MasterClass that awards certificates",
            date=date.today() - timedelta(days=1),  # Past event
            start_time=time(10, 0),
            end_time=time(12, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/cert",
            instructor_id="mc_instructor",
            is_certificate=True,
            diploma_template_id="MC_CERT",
        )
        database.session.add(masterclass)
        database.session.commit()
        
        # Create certification
        certification = Certificacion(
            usuario="mc_student",
            master_class_id=masterclass.id,
            certificado="MC_CERT",
            fecha=date.today(),
        )
        database.session.add(certification)
        database.session.commit()
        
        # Verify certification
        retrieved = database.session.execute(
            database.select(Certificacion).filter_by(
                usuario="mc_student",
                master_class_id=masterclass.id
            )
        ).scalar_one()
        
        assert retrieved.get_content_type() == "masterclass"
        assert retrieved.certificado == "MC_CERT"

    def test_masterclass_certification_content_info(self, app_context):
        """Test getting MasterClass information from certification."""
        # Create template
        template = Certificado(
            code="MC_INFO_CERT",
            titulo="MasterClass Info Certificate",
            habilitado=True,
        )
        
        # Create instructor and student
        instructor = Usuario(
            usuario="info_mc_instructor",
            acceso=b"infomcpass123",
            nombre="InfoMC",
            apellido="Instructor",
            correo_electronico="infomc@instructor.com",
            tipo="instructor",
            activo=True,
        )
        
        student = Usuario(
            usuario="info_mc_student",
            acceso=b"infomcstudent123",
            nombre="InfoMC",
            apellido="Student",
            correo_electronico="infomc@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([template, instructor, student])
        database.session.commit()
        
        # Create MasterClass
        masterclass = MasterClass(
            titulo="Information Test MasterClass",
            slug="info-test-masterclass",
            description_public="MasterClass for testing information retrieval",
            date=date.today() - timedelta(days=2),
            start_time=time(14, 0),
            end_time=time(16, 0),
            platform_name="Google Meet",
            platform_url="https://meet.google.com/info",
            instructor_id="info_mc_instructor",
            is_certificate=True,
        )
        database.session.add(masterclass)
        database.session.commit()
        
        # Create certification
        certification = Certificacion(
            usuario="info_mc_student",
            master_class_id=masterclass.id,
            certificado="MC_INFO_CERT",
            fecha=date.today(),
        )
        database.session.add(certification)
        database.session.commit()
        
        # Test content info retrieval
        content_info = certification.get_content_info()
        assert content_info is not None
        assert content_info.title == "Information Test MasterClass"
        assert content_info.slug == "info-test-masterclass"

    def test_multiple_masterclass_certifications(self, app_context):
        """Test student with multiple MasterClass certifications."""
        # Create template
        template = Certificado(code="MULTI_MC_CERT", titulo="Multi MasterClass Cert", habilitado=True)
        
        # Create instructor
        instructor = Usuario(
            usuario="multi_mc_instructor",
            acceso=b"multimcpass123",
            nombre="MultiMC",
            apellido="Instructor",
            correo_electronico="multimc@instructor.com",
            tipo="instructor",
            activo=True,
        )
        
        # Create student
        student = Usuario(
            usuario="multi_mc_student",
            acceso=b"multimcstudent123",
            nombre="MultiMC",
            apellido="Student",
            correo_electronico="multimc@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([template, instructor, student])
        database.session.commit()
        
        # Create multiple MasterClasses
        mc1 = MasterClass(
            titulo="Multi MasterClass 1",
            slug="multi-mc-1",
            description_public="First MasterClass",
            date=date.today() - timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/multi1",
            instructor_id="multi_mc_instructor",
            is_certificate=True,
        )
        
        mc2 = MasterClass(
            titulo="Multi MasterClass 2",
            slug="multi-mc-2",
            description_public="Second MasterClass",
            date=date.today() - timedelta(days=3),
            start_time=time(14, 0),
            end_time=time(16, 0),
            platform_name="Google Meet",
            platform_url="https://meet.google.com/multi2",
            instructor_id="multi_mc_instructor",
            is_certificate=True,
        )
        
        database.session.add_all([mc1, mc2])
        database.session.commit()
        
        # Create certifications
        cert1 = Certificacion(
            usuario="multi_mc_student",
            master_class_id=mc1.id,
            certificado="MULTI_MC_CERT",
            fecha=date.today() - timedelta(days=6),
        )
        
        cert2 = Certificacion(
            usuario="multi_mc_student",
            master_class_id=mc2.id,
            certificado="MULTI_MC_CERT",
            fecha=date.today() - timedelta(days=2),
        )
        
        database.session.add_all([cert1, cert2])
        database.session.commit()
        
        # Verify multiple certifications
        certifications = database.session.execute(
            database.select(Certificacion).filter_by(usuario="multi_mc_student")
        ).scalars().all()
        
        assert len(certifications) == 2
        assert all(cert.get_content_type() == "masterclass" for cert in certifications)


class TestMixedCertifications:
    """Test certifications for both courses and MasterClasses."""

    def test_student_with_mixed_certifications(self, app_context):
        """Test student with both course and MasterClass certifications."""
        # Create templates
        course_template = Certificado(code="MIXED_COURSE_CERT", titulo="Mixed Course Cert", habilitado=True)
        mc_template = Certificado(code="MIXED_MC_CERT", titulo="Mixed MC Cert", habilitado=True)
        
        # Create course
        course = Curso(
            codigo="MIXED_COURSE",
            nombre="Mixed Course",
            descripcion="Course for mixed testing",
            estado="finalized",
            certificado=True,
        )
        
        # Create instructor and student
        instructor = Usuario(
            usuario="mixed_instructor",
            acceso=b"mixedpass123",
            nombre="Mixed",
            apellido="Instructor",
            correo_electronico="mixed@instructor.com",
            tipo="instructor",
            activo=True,
        )
        
        student = Usuario(
            usuario="mixed_student",
            acceso=b"mixedstudent123",
            nombre="Mixed",
            apellido="Student",
            correo_electronico="mixed@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([course_template, mc_template, course, instructor, student])
        database.session.commit()
        
        # Create MasterClass
        masterclass = MasterClass(
            titulo="Mixed MasterClass",
            slug="mixed-masterclass",
            description_public="MasterClass for mixed testing",
            date=date.today() - timedelta(days=5),
            start_time=time(9, 0),
            end_time=time(11, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/mixed",
            instructor_id="mixed_instructor",
            is_certificate=True,
        )
        database.session.add(masterclass)
        database.session.commit()
        
        # Create both types of certifications
        course_cert = Certificacion(
            usuario="mixed_student",
            curso="MIXED_COURSE",
            certificado="MIXED_COURSE_CERT",
            fecha=date.today() - timedelta(days=10),
            nota=Decimal("89.0"),
        )
        
        mc_cert = Certificacion(
            usuario="mixed_student",
            master_class_id=masterclass.id,
            certificado="MIXED_MC_CERT",
            fecha=date.today() - timedelta(days=4),
        )
        
        database.session.add_all([course_cert, mc_cert])
        database.session.commit()
        
        # Verify mixed certifications
        all_certs = database.session.execute(
            database.select(Certificacion).filter_by(usuario="mixed_student")
        ).scalars().all()
        
        assert len(all_certs) == 2
        
        # Check different content types
        content_types = [cert.get_content_type() for cert in all_certs]
        assert "course" in content_types
        assert "masterclass" in content_types
        
        # Verify course certification has grade
        course_certs = [cert for cert in all_certs if cert.get_content_type() == "course"]
        assert len(course_certs) == 1
        assert course_certs[0].nota == Decimal("89.0")
        
        # Verify MasterClass certification
        mc_certs = [cert for cert in all_certs if cert.get_content_type() == "masterclass"]
        assert len(mc_certs) == 1
        assert mc_certs[0].nota is None  # MasterClasses typically don't have grades


class TestCertificationValidationAndConstraints:
    """Test certification validation rules and constraints."""

    def test_certification_required_fields(self, app_context):
        """Test that required fields are enforced."""
        # Create basic dependencies
        template = Certificado(code="REQ_CERT", titulo="Required Cert", habilitado=True)
        student = Usuario(
            usuario="req_student",
            acceso=b"reqpass123",
            nombre="Required",
            apellido="Student",
            correo_electronico="req@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([template, student])
        database.session.commit()
        
        # Certification without usuario should fail
        with pytest.raises(Exception):
            cert = Certificacion(
                curso="SOME_COURSE",
                certificado="REQ_CERT",
                fecha=date.today(),
            )
            database.session.add(cert)
            database.session.commit()

    def test_certification_content_type_validation(self, app_context):
        """Test that certification must have either course or masterclass."""
        template = Certificado(code="CONTENT_CERT", titulo="Content Cert", habilitado=True)
        student = Usuario(
            usuario="content_student",
            acceso=b"contentpass123",
            nombre="Content",
            apellido="Student",
            correo_electronico="content@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([template, student])
        database.session.commit()
        
        # Valid certification with course
        course_cert = Certificacion(
            usuario="content_student",
            curso="VALID_COURSE",
            certificado="CONTENT_CERT",
            fecha=date.today(),
        )
        database.session.add(course_cert)
        database.session.commit()
        
        # Verify it works
        assert course_cert.get_content_type() == "course"
        
        # Test get_content_info with non-existent course returns None
        assert course_cert.get_content_info() is None

    def test_certification_date_validation(self, app_context):
        """Test certification date handling."""
        template = Certificado(code="DATE_CERT", titulo="Date Cert", habilitado=True)
        course = Curso(codigo="DATE_COURSE", nombre="Date Course", estado="finalized", certificado=True)
        student = Usuario(
            usuario="date_student",
            acceso=b"datepass123",
            nombre="Date",
            apellido="Student",
            correo_electronico="date@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([template, course, student])
        database.session.commit()
        
        # Test with specific date
        specific_date = date(2024, 6, 15)
        cert = Certificacion(
            usuario="date_student",
            curso="DATE_COURSE",
            certificado="DATE_CERT",
            fecha=specific_date,
            nota=Decimal("91.5"),
        )
        database.session.add(cert)
        database.session.commit()
        
        # Verify specific date
        retrieved = database.session.execute(
            database.select(Certificacion).filter_by(usuario="date_student")
        ).scalar_one()
        
        assert retrieved.fecha == specific_date

    def test_certification_grade_validation(self, app_context):
        """Test certification grade (nota) validation."""
        template = Certificado(code="GRADE_VALID_CERT", titulo="Grade Valid Cert", habilitado=True)
        course = Curso(codigo="GRADE_VALID_COURSE", nombre="Grade Valid Course", estado="finalized", certificado=True)
        student = Usuario(
            usuario="grade_valid_student",
            acceso=b"gradevalidpass123",
            nombre="GradeValid",
            apellido="Student",
            correo_electronico="gradevalid@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([template, course, student])
        database.session.commit()
        
        # Test with decimal grade
        cert = Certificacion(
            usuario="grade_valid_student",
            curso="GRADE_VALID_COURSE",
            certificado="GRADE_VALID_CERT",
            fecha=date.today(),
            nota=Decimal("87.75"),
        )
        database.session.add(cert)
        database.session.commit()
        
        # Verify decimal grade precision
        retrieved = database.session.execute(
            database.select(Certificacion).filter_by(usuario="grade_valid_student")
        ).scalar_one()
        
        assert retrieved.nota == Decimal("87.75")

    def test_certification_without_content_reference(self, app_context):
        """Test certification content type when neither course nor masterclass is set."""
        template = Certificado(code="NO_CONTENT_CERT", titulo="No Content Cert", habilitado=True)
        student = Usuario(
            usuario="no_content_student",
            acceso=b"nocontentpass123",
            nombre="NoContent",
            apellido="Student",
            correo_electronico="nocontent@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([template, student])
        database.session.commit()
        
        # Create certification without course or masterclass reference
        cert = Certificacion(
            usuario="no_content_student",
            certificado="NO_CONTENT_CERT",
            fecha=date.today(),
        )
        database.session.add(cert)
        database.session.commit()
        
        # Test methods with no content
        assert cert.get_content_type() is None
        assert cert.get_content_info() is None


class TestCertificationQueryAndRetrieval:
    """Test certification querying and retrieval patterns."""

    def test_find_certifications_by_user(self, app_context):
        """Test finding all certifications for a specific user."""
        # Create templates
        template1 = Certificado(code="QUERY_CERT1", titulo="Query Cert 1", habilitado=True)
        template2 = Certificado(code="QUERY_CERT2", titulo="Query Cert 2", habilitado=True)
        
        # Create courses
        course1 = Curso(codigo="QUERY_COURSE1", nombre="Query Course 1", estado="finalized", certificado=True)
        course2 = Curso(codigo="QUERY_COURSE2", nombre="Query Course 2", estado="finalized", certificado=True)
        
        # Create student
        student = Usuario(
            usuario="query_student",
            acceso=b"querypass123",
            nombre="Query",
            apellido="Student",
            correo_electronico="query@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([template1, template2, course1, course2, student])
        database.session.commit()
        
        # Create certifications
        cert1 = Certificacion(
            usuario="query_student",
            curso="QUERY_COURSE1",
            certificado="QUERY_CERT1",
            fecha=date.today() - timedelta(days=20),
            nota=Decimal("85.0"),
        )
        
        cert2 = Certificacion(
            usuario="query_student",
            curso="QUERY_COURSE2",
            certificado="QUERY_CERT2",
            fecha=date.today() - timedelta(days=10),
            nota=Decimal("92.5"),
        )
        
        database.session.add_all([cert1, cert2])
        database.session.commit()
        
        # Query all certifications for user
        user_certs = database.session.execute(
            database.select(Certificacion).filter_by(usuario="query_student").order_by(Certificacion.fecha.desc())
        ).scalars().all()
        
        assert len(user_certs) == 2
        # Most recent should be first
        assert user_certs[0].curso == "QUERY_COURSE2"
        assert user_certs[1].curso == "QUERY_COURSE1"

    def test_find_certifications_by_course(self, app_context):
        """Test finding all certifications for a specific course."""
        # Create template and course
        template = Certificado(code="COURSE_QUERY_CERT", titulo="Course Query Cert", habilitado=True)
        course = Curso(codigo="COURSE_QUERY", nombre="Course Query", estado="finalized", certificado=True)
        
        # Create students
        student1 = Usuario(
            usuario="course_query_student1",
            acceso=b"coursequery1pass123",
            nombre="CourseQuery1",
            apellido="Student",
            correo_electronico="coursequery1@student.com",
            tipo="user",
            activo=True,
        )
        
        student2 = Usuario(
            usuario="course_query_student2",
            acceso=b"coursequery2pass123",
            nombre="CourseQuery2",
            apellido="Student",
            correo_electronico="coursequery2@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([template, course, student1, student2])
        database.session.commit()
        
        # Create certifications for same course
        cert1 = Certificacion(
            usuario="course_query_student1",
            curso="COURSE_QUERY",
            certificado="COURSE_QUERY_CERT",
            fecha=date.today(),
            nota=Decimal("78.0"),
        )
        
        cert2 = Certificacion(
            usuario="course_query_student2",
            curso="COURSE_QUERY",
            certificado="COURSE_QUERY_CERT",
            fecha=date.today(),
            nota=Decimal("94.5"),
        )
        
        database.session.add_all([cert1, cert2])
        database.session.commit()
        
        # Query all certifications for course
        course_certs = database.session.execute(
            database.select(Certificacion).filter_by(curso="COURSE_QUERY").order_by(Certificacion.nota.desc())
        ).scalars().all()
        
        assert len(course_certs) == 2
        # Highest grade should be first
        assert course_certs[0].nota == Decimal("94.5")
        assert course_certs[1].nota == Decimal("78.0")

    def test_find_certifications_by_date_range(self, app_context):
        """Test finding certifications within a date range."""
        # Create template and course
        template = Certificado(code="DATE_RANGE_CERT", titulo="Date Range Cert", habilitado=True)
        course = Curso(codigo="DATE_RANGE_COURSE", nombre="Date Range Course", estado="finalized", certificado=True)
        student = Usuario(
            usuario="date_range_student",
            acceso=b"daterangepass123",
            nombre="DateRange",
            apellido="Student",
            correo_electronico="daterange@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([template, course, student])
        database.session.commit()
        
        # Create certifications with different dates
        old_cert = Certificacion(
            usuario="date_range_student",
            curso="DATE_RANGE_COURSE",
            certificado="DATE_RANGE_CERT",
            fecha=date.today() - timedelta(days=60),
        )
        
        recent_cert = Certificacion(
            usuario="date_range_student",
            curso="DATE_RANGE_COURSE",
            certificado="DATE_RANGE_CERT",
            fecha=date.today() - timedelta(days=5),
        )
        
        database.session.add_all([old_cert, recent_cert])
        database.session.commit()
        
        # Query certifications within last 30 days
        thirty_days_ago = date.today() - timedelta(days=30)
        recent_certs = database.session.execute(
            database.select(Certificacion).filter(
                Certificacion.usuario == "date_range_student",
                Certificacion.fecha >= thirty_days_ago
            )
        ).scalars().all()
        
        assert len(recent_certs) == 1
        assert recent_certs[0].fecha == date.today() - timedelta(days=5)


class TestCertificationStatisticsAndReporting:
    """Test certification statistics and reporting functionality."""

    def test_certification_count_by_template(self, app_context):
        """Test counting certifications by template."""
        # Create templates
        popular_template = Certificado(code="POPULAR_CERT", titulo="Popular Cert", habilitado=True)
        rare_template = Certificado(code="RARE_CERT", titulo="Rare Cert", habilitado=True)
        
        # Create courses
        course1 = Curso(codigo="POP_COURSE", nombre="Popular Course", estado="finalized", certificado=True)
        course2 = Curso(codigo="RARE_COURSE", nombre="Rare Course", estado="finalized", certificado=True)
        
        # Create students
        students = []
        for i in range(5):
            student = Usuario(
                usuario=f"stat_student_{i}",
                acceso=b"statpass123",
                nome=f"Stat{i}",
                apellido="Student",
                correo_electronico=f"stat{i}@student.com",
                tipo="user",
                activo=True,
            )
            students.append(student)
        
        database.session.add_all([popular_template, rare_template, course1, course2] + students)
        database.session.commit()
        
        # Create certifications - more for popular template
        popular_certs = []
        for i in range(4):
            cert = Certificacion(
                usuario=f"stat_student_{i}",
                curso="POP_COURSE",
                certificado="POPULAR_CERT",
                fecha=date.today(),
                nota=Decimal("85.0"),
            )
            popular_certs.append(cert)
        
        # One certification for rare template
        rare_cert = Certificacion(
            usuario="stat_student_4",
            curso="RARE_COURSE",
            certificado="RARE_CERT",
            fecha=date.today(),
            nota=Decimal("90.0"),
        )
        
        database.session.add_all(popular_certs + [rare_cert])
        database.session.commit()
        
        # Count certifications by template
        from sqlalchemy import func
        
        template_counts = database.session.execute(
            database.select(
                Certificacion.certificado,
                func.count(Certificacion.id).label('count')
            ).group_by(Certificacion.certificado)
        ).all()
        
        template_count_dict = {row[0]: row[1] for row in template_counts}
        
        assert template_count_dict["POPULAR_CERT"] == 4
        assert template_count_dict["RARE_CERT"] == 1

    def test_average_grade_by_course(self, app_context):
        """Test calculating average grade by course."""
        # Create template and course
        template = Certificado(code="AVG_CERT", titulo="Average Cert", habilitado=True)
        course = Curso(codigo="AVG_COURSE", nombre="Average Course", estado="finalized", certificado=True)
        
        # Create students
        students = []
        for i in range(3):
            student = Usuario(
                usuario=f"avg_student_{i}",
                acceso=b"avgpass123",
                nome=f"Avg{i}",
                apellido="Student",
                correo_electronico=f"avg{i}@student.com",
                tipo="user",
                activo=True,
            )
            students.append(student)
        
        database.session.add_all([template, course] + students)
        database.session.commit()
        
        # Create certifications with different grades
        grades = [Decimal("80.0"), Decimal("90.0"), Decimal("85.0")]
        certs = []
        for i, grade in enumerate(grades):
            cert = Certificacion(
                usuario=f"avg_student_{i}",
                curso="AVG_COURSE",
                certificado="AVG_CERT",
                fecha=date.today(),
                nota=grade,
            )
            certs.append(cert)
        
        database.session.add_all(certs)
        database.session.commit()
        
        # Calculate average grade
        from sqlalchemy import func
        
        avg_grade = database.session.execute(
            database.select(func.avg(Certificacion.nota)).filter_by(curso="AVG_COURSE")
        ).scalar()
        
        expected_avg = sum(grades) / len(grades)
        assert abs(float(avg_grade) - float(expected_avg)) < 0.01  # Allow small floating point differences