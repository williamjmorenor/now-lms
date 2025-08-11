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

"""Comprehensive tests for MasterClass functionality."""

import pytest
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from now_lms.db import (
    MasterClass,
    MasterClassEnrollment,
    Usuario,
    Certificacion,
    Certificado,
    Pago,
    database,
)


class TestMasterClassBasicFunctionality:
    """Test basic MasterClass model and creation."""

    def test_masterclass_model_exists(self, app_context):
        """Test that MasterClass model can be imported and instantiated."""
        instructor = Usuario(
            usuario="mc_instructor",
            acceso=b"password123",
            nombre="MasterClass",
            apellido="Instructor",
            correo_electronico="instructor@masterclass.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        masterclass = MasterClass(
            title="Test MasterClass",
            slug="test-masterclass",
            description_public="A comprehensive test masterclass",
            date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/j/123456789",
            instructor_id="mc_instructor",
        )
        
        assert masterclass is not None
        assert masterclass.title == "Test MasterClass"
        assert masterclass.slug == "test-masterclass"

    def test_masterclass_creation_with_database(self, app_context):
        """Test MasterClass creation and persistence in database."""
        # Create instructor
        instructor = Usuario(
            usuario="db_instructor",
            acceso=b"dbpass123",
            nombre="Database",
            apellido="Instructor",
            correo_electronico="db@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        # Create MasterClass
        masterclass = MasterClass(
            title="Database MasterClass",
            slug="database-masterclass",
            description_public="Testing database persistence for masterclasses",
            description_private="Internal notes for instructors",
            date=date.today() + timedelta(days=14),
            start_time=time(14, 30),
            end_time=time(16, 30),
            platform_name="Google Meet",
            platform_url="https://meet.google.com/abc-defg-hij",
            instructor_id="db_instructor",
            is_certificate=True,
        )
        
        database.session.add(masterclass)
        database.session.commit()
        
        # Retrieve and verify
        retrieved = database.session.execute(
            database.select(MasterClass).filter_by(slug="database-masterclass")
        ).scalar_one()
        
        assert retrieved.title == "Database MasterClass"
        assert retrieved.platform_name == "Google Meet"
        assert retrieved.is_certificate is True
        assert retrieved.instructor_id == "db_instructor"

    def test_masterclass_always_free(self, app_context):
        """Test that MasterClasses are always free (marketing strategy)."""
        instructor = Usuario(
            usuario="free_instructor",
            acceso=b"freepass123",
            nombre="Free",
            apellido="Instructor",
            correo_electronico="free@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        # Even if we set payment configuration, effective price should be 0
        masterclass = MasterClass(
            title="Free MasterClass",
            slug="free-masterclass",
            description_public="This masterclass is free",
            date=date.today() + timedelta(days=3),
            start_time=time(9, 0),
            end_time=time(11, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/j/987654321",
            instructor_id="free_instructor",
            is_paid=True,  # This is ignored
            price=Decimal("50.00"),  # This is ignored
        )
        
        database.session.add(masterclass)
        database.session.commit()
        
        # Effective price should be 0 regardless of configuration
        assert masterclass.get_effective_price() == 0


class TestMasterClassSchedulingAndTiming:
    """Test MasterClass scheduling and time management."""

    def test_masterclass_timing_methods(self, app_context):
        """Test upcoming, ongoing, and finished status methods."""
        instructor = Usuario(
            usuario="timing_instructor",
            acceso=b"timepass123",
            nombre="Timing",
            apellido="Instructor",
            correo_electronico="timing@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        # Future MasterClass
        future_mc = MasterClass(
            title="Future MasterClass",
            slug="future-masterclass",
            description_public="This is in the future",
            date=date.today() + timedelta(days=10),
            start_time=time(10, 0),
            end_time=time(12, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/future",
            instructor_id="timing_instructor",
        )
        
        # Past MasterClass
        past_mc = MasterClass(
            title="Past MasterClass",
            slug="past-masterclass",
            description_public="This is in the past",
            date=date.today() - timedelta(days=5),
            start_time=time(10, 0),
            end_time=time(12, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/past",
            instructor_id="timing_instructor",
        )
        
        database.session.add_all([future_mc, past_mc])
        database.session.commit()
        
        # Test timing methods
        assert future_mc.is_upcoming() is True
        assert future_mc.is_ongoing() is False
        assert future_mc.is_finished() is False
        
        assert past_mc.is_upcoming() is False
        assert past_mc.is_ongoing() is False
        assert past_mc.is_finished() is True

    def test_masterclass_today_timing(self, app_context):
        """Test timing for MasterClass happening today."""
        instructor = Usuario(
            usuario="today_instructor",
            acceso=b"todaypass123",
            nombre="Today",
            apellido="Instructor",
            correo_electronico="today@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        # Create a MasterClass for today but in the future
        today_future = MasterClass(
            title="Today Future MasterClass",
            slug="today-future",
            description_public="Today but later",
            date=date.today(),
            start_time=time(23, 59),  # Very late today
            end_time=time(23, 59),
            platform_name="Zoom",
            platform_url="https://zoom.us/today-future",
            instructor_id="today_instructor",
        )
        
        # Create a MasterClass for today but in the past
        today_past = MasterClass(
            title="Today Past MasterClass",
            slug="today-past",
            description_public="Today but earlier",
            date=date.today(),
            start_time=time(0, 1),  # Very early today
            end_time=time(0, 2),
            platform_name="Zoom",
            platform_url="https://zoom.us/today-past",
            instructor_id="today_instructor",
        )
        
        database.session.add_all([today_future, today_past])
        database.session.commit()
        
        # The exact results depend on current time, but we can test the logic
        # The past one should definitely be finished
        assert today_past.is_finished() is True


class TestMasterClassEnrollmentSystem:
    """Test MasterClass enrollment functionality."""

    def test_student_enrollment(self, app_context):
        """Test student enrollment in MasterClass."""
        # Create instructor and student
        instructor = Usuario(
            usuario="enroll_instructor",
            acceso=b"enrollpass123",
            nombre="Enrollment",
            apellido="Instructor",
            correo_electronico="enroll@instructor.com",
            tipo="instructor",
            activo=True,
        )
        
        student = Usuario(
            usuario="mc_student",
            acceso=b"studentpass123",
            nombre="MasterClass",
            apellido="Student",
            correo_electronico="student@masterclass.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([instructor, student])
        database.session.commit()

        # Create MasterClass
        masterclass = MasterClass(
            title="Enrollment Test MasterClass",
            slug="enrollment-test",
            description_public="Testing enrollment functionality",
            date=date.today() + timedelta(days=7),
            start_time=time(15, 0),
            end_time=time(17, 0),
            platform_name="Google Meet",
            platform_url="https://meet.google.com/enrollment-test",
            instructor_id="enroll_instructor",
        )
        database.session.add(masterclass)
        database.session.commit()

        # Enroll student
        enrollment = MasterClassEnrollment(
            master_class_id=masterclass.id,
            user_id="mc_student",
            is_confirmed=True,
        )
        database.session.add(enrollment)
        database.session.commit()
        
        # Verify enrollment
        enrolled = database.session.execute(
            database.select(MasterClassEnrollment).filter_by(
                master_class_id=masterclass.id,
                user_id="mc_student"
            )
        ).scalar_one()
        
        assert enrolled is not None
        assert enrolled.is_confirmed is True
        assert enrolled.user_id == "mc_student"

    def test_enrollment_uniqueness_constraint(self, app_context):
        """Test that a user can only enroll once per MasterClass."""
        # Create instructor and student
        instructor = Usuario(
            usuario="unique_instructor",
            acceso=b"uniquepass123",
            nombre="Unique",
            apellido="Instructor",
            correo_electronico="unique@instructor.com",
            tipo="instructor",
            activo=True,
        )
        
        student = Usuario(
            usuario="unique_student",
            acceso=b"uniquestudent123",
            nombre="Unique",
            apellido="Student",
            correo_electronico="unique@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([instructor, student])
        database.session.commit()

        # Create MasterClass
        masterclass = MasterClass(
            title="Unique Enrollment Test",
            slug="unique-enrollment",
            description_public="Testing enrollment uniqueness",
            date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/unique",
            instructor_id="unique_instructor",
        )
        database.session.add(masterclass)
        database.session.commit()

        # First enrollment should succeed
        enrollment1 = MasterClassEnrollment(
            master_class_id=masterclass.id,
            user_id="unique_student",
            is_confirmed=True,
        )
        database.session.add(enrollment1)
        database.session.commit()

        # Second enrollment for same user should fail
        enrollment2 = MasterClassEnrollment(
            master_class_id=masterclass.id,
            user_id="unique_student",
            is_confirmed=False,
        )
        database.session.add(enrollment2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            database.session.commit()

    def test_enrollment_confirmation_status(self, app_context):
        """Test enrollment confirmation workflow."""
        # Create instructor and student
        instructor = Usuario(
            usuario="confirm_instructor",
            acceso=b"confirmpass123",
            nombre="Confirm",
            apellido="Instructor",
            correo_electronico="confirm@instructor.com",
            tipo="instructor",
            activo=True,
        )
        
        student = Usuario(
            usuario="confirm_student",
            acceso=b"confirmstudent123",
            nombre="Confirm",
            apellido="Student",
            correo_electronico="confirm@student.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([instructor, student])
        database.session.commit()

        # Create MasterClass
        masterclass = MasterClass(
            title="Confirmation Test",
            slug="confirmation-test",
            description_public="Testing enrollment confirmation",
            date=date.today() + timedelta(days=7),
            start_time=time(13, 0),
            end_time=time(15, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/confirm",
            instructor_id="confirm_instructor",
        )
        database.session.add(masterclass)
        database.session.commit()

        # Create unconfirmed enrollment
        enrollment = MasterClassEnrollment(
            master_class_id=masterclass.id,
            user_id="confirm_student",
            is_confirmed=False,
        )
        database.session.add(enrollment)
        database.session.commit()
        
        # Verify unconfirmed status
        enrolled = database.session.execute(
            database.select(MasterClassEnrollment).filter_by(
                master_class_id=masterclass.id,
                user_id="confirm_student"
            )
        ).scalar_one()
        
        assert enrolled.is_confirmed is False
        
        # Confirm enrollment
        enrolled.is_confirmed = True
        database.session.commit()
        
        # Verify confirmation
        confirmed = database.session.execute(
            database.select(MasterClassEnrollment).filter_by(
                master_class_id=masterclass.id,
                user_id="confirm_student"
            )
        ).scalar_one()
        
        assert confirmed.is_confirmed is True


class TestMasterClassCertificationSystem:
    """Test MasterClass certificate generation and management."""

    def test_masterclass_with_certificate_configuration(self, app_context):
        """Test MasterClass certificate configuration."""
        # Create certificate template
        cert_template = Certificado(
            code="MC_CERT_TEMPLATE",
            title="MasterClass Certificate",
            habilitado=True,
            publico=True,
        )
        database.session.add(cert_template)
        database.session.commit()

        # Create instructor
        instructor = Usuario(
            usuario="cert_instructor",
            acceso=b"certpass123",
            nombre="Certificate",
            apellido="Instructor",
            correo_electronico="cert@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        # Create MasterClass with certificate
        masterclass = MasterClass(
            title="Certificate MasterClass",
            slug="certificate-masterclass",
            description_public="MasterClass that awards certificates",
            date=date.today() + timedelta(days=7),
            start_time=time(9, 0),
            end_time=time(11, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/certificate",
            instructor_id="cert_instructor",
            is_certificate=True,
            diploma_template_id="MC_CERT_TEMPLATE",
        )
        database.session.add(masterclass)
        database.session.commit()
        
        # Verify certificate configuration
        retrieved = database.session.execute(
            database.select(MasterClass).filter_by(slug="certificate-masterclass")
        ).scalar_one()
        
        assert retrieved.is_certificate is True
        assert retrieved.diploma_template_id == "MC_CERT_TEMPLATE"

    def test_certificate_generation_for_masterclass(self, app_context):
        """Test certificate generation for MasterClass completion."""
        # Create certificate template
        cert_template = Certificado(
            code="MC_GEN_TEMPLATE",
            title="Generated MasterClass Certificate",
            habilitado=True,
        )
        database.session.add(cert_template)

        # Create instructor
        instructor = Usuario(
            usuario="gen_instructor",
            acceso=b"genpass123",
            nombre="Generation",
            apellido="Instructor",
            correo_electronico="gen@instructor.com",
            tipo="instructor",
            activo=True,
        )
        
        # Create student
        student = Usuario(
            usuario="cert_mc_student",
            acceso=b"certstudent123",
            nombre="Certificate",
            apellido="Student",
            correo_electronico="certstudent@masterclass.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([instructor, student])
        database.session.commit()

        # Create MasterClass with certificate
        masterclass = MasterClass(
            title="Certificate Generation Test",
            slug="cert-generation-test",
            description_public="Testing certificate generation",
            date=date.today() - timedelta(days=1),  # Past event
            start_time=time(10, 0),
            end_time=time(12, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/cert-gen",
            instructor_id="gen_instructor",
            is_certificate=True,
            diploma_template_id="MC_GEN_TEMPLATE",
        )
        database.session.add(masterclass)
        database.session.commit()

        # Enroll student
        enrollment = MasterClassEnrollment(
            master_class_id=masterclass.id,
            user_id="cert_mc_student",
            is_confirmed=True,
        )
        database.session.add(enrollment)
        database.session.commit()

        # Generate certificate for completed MasterClass
        certification = Certificacion(
            usuario="cert_mc_student",
            master_class_id=masterclass.id,
            certificado="MC_GEN_TEMPLATE",
            fecha=date.today(),
        )
        database.session.add(certification)
        database.session.commit()
        
        # Verify certificate
        generated_cert = database.session.execute(
            database.select(Certificacion).filter_by(
                usuario="cert_mc_student",
                master_class_id=masterclass.id
            )
        ).scalar_one()
        
        assert generated_cert is not None
        assert generated_cert.get_content_type() == "masterclass"
        
        # Test get_content_info method
        content_info = generated_cert.get_content_info()
        assert content_info is not None
        assert content_info.title == "Certificate Generation Test"


class TestMasterClassPlatformIntegration:
    """Test MasterClass platform integration (Zoom, Google Meet, etc.)."""

    def test_zoom_platform_configuration(self, app_context):
        """Test Zoom platform configuration."""
        instructor = Usuario(
            usuario="zoom_instructor",
            acceso=b"zoompass123",
            nombre="Zoom",
            apellido="Instructor",
            correo_electronico="zoom@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        zoom_masterclass = MasterClass(
            title="Zoom MasterClass",
            slug="zoom-masterclass",
            description_public="MasterClass on Zoom platform",
            date=date.today() + timedelta(days=7),
            start_time=time(14, 0),
            end_time=time(16, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/j/123456789?pwd=abcdef123456",
            instructor_id="zoom_instructor",
        )
        database.session.add(zoom_masterclass)
        database.session.commit()
        
        # Verify Zoom configuration
        retrieved = database.session.execute(
            database.select(MasterClass).filter_by(slug="zoom-masterclass")
        ).scalar_one()
        
        assert retrieved.platform_name == "Zoom"
        assert "zoom.us" in retrieved.platform_url

    def test_google_meet_platform_configuration(self, app_context):
        """Test Google Meet platform configuration."""
        instructor = Usuario(
            usuario="meet_instructor",
            acceso=b"meetpass123",
            nombre="Meet",
            apellido="Instructor",
            correo_electronico="meet@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        meet_masterclass = MasterClass(
            title="Google Meet MasterClass",
            slug="meet-masterclass",
            description_public="MasterClass on Google Meet platform",
            date=date.today() + timedelta(days=7),
            start_time=time(11, 0),
            end_time=time(13, 0),
            platform_name="Google Meet",
            platform_url="https://meet.google.com/abc-defg-hij",
            instructor_id="meet_instructor",
        )
        database.session.add(meet_masterclass)
        database.session.commit()
        
        # Verify Google Meet configuration
        retrieved = database.session.execute(
            database.select(MasterClass).filter_by(slug="meet-masterclass")
        ).scalar_one()
        
        assert retrieved.platform_name == "Google Meet"
        assert "meet.google.com" in retrieved.platform_url

    def test_custom_platform_configuration(self, app_context):
        """Test custom platform configuration."""
        instructor = Usuario(
            usuario="custom_instructor",
            acceso=b"custompass123",
            nombre="Custom",
            apellido="Instructor",
            correo_electronico="custom@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        custom_masterclass = MasterClass(
            title="Custom Platform MasterClass",
            slug="custom-masterclass",
            description_public="MasterClass on custom platform",
            date=date.today() + timedelta(days=7),
            start_time=time(16, 0),
            end_time=time(18, 0),
            platform_name="Teams",
            platform_url="https://teams.microsoft.com/l/meetup-join/custom-link",
            instructor_id="custom_instructor",
        )
        database.session.add(custom_masterclass)
        database.session.commit()
        
        # Verify custom platform configuration
        retrieved = database.session.execute(
            database.select(MasterClass).filter_by(slug="custom-masterclass")
        ).scalar_one()
        
        assert retrieved.platform_name == "Teams"
        assert "teams.microsoft.com" in retrieved.platform_url


class TestMasterClassMediaAndRecording:
    """Test MasterClass media management and recording features."""

    def test_masterclass_with_cover_image(self, app_context):
        """Test MasterClass with cover image configuration."""
        instructor = Usuario(
            usuario="image_instructor",
            acceso=b"imagepass123",
            nombre="Image",
            apellido="Instructor",
            correo_electronico="image@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        image_masterclass = MasterClass(
            title="Image MasterClass",
            slug="image-masterclass",
            description_public="MasterClass with cover image",
            date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/image",
            instructor_id="image_instructor",
            image_path="/uploads/masterclass/cover_image.jpg",
        )
        database.session.add(image_masterclass)
        database.session.commit()
        
        # Verify image configuration
        retrieved = database.session.execute(
            database.select(MasterClass).filter_by(slug="image-masterclass")
        ).scalar_one()
        
        assert retrieved.image_path == "/uploads/masterclass/cover_image.jpg"

    def test_masterclass_with_recording(self, app_context):
        """Test MasterClass with video recording URL."""
        instructor = Usuario(
            usuario="record_instructor",
            acceso=b"recordpass123",
            nombre="Recording",
            apellido="Instructor",
            correo_electronico="record@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        # Past MasterClass with recording
        recorded_masterclass = MasterClass(
            title="Recorded MasterClass",
            slug="recorded-masterclass",
            description_public="Past MasterClass with recording",
            date=date.today() - timedelta(days=7),
            start_time=time(14, 0),
            end_time=time(16, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/recorded",
            instructor_id="record_instructor",
            video_recording_url="https://vimeo.com/123456789",
        )
        database.session.add(recorded_masterclass)
        database.session.commit()
        
        # Verify recording configuration
        retrieved = database.session.execute(
            database.select(MasterClass).filter_by(slug="recorded-masterclass")
        ).scalar_one()
        
        assert retrieved.video_recording_url == "https://vimeo.com/123456789"
        assert retrieved.is_finished() is True


class TestMasterClassValidationAndConstraints:
    """Test MasterClass validation rules and database constraints."""

    def test_masterclass_slug_uniqueness(self, app_context):
        """Test that MasterClass slugs must be unique."""
        instructor = Usuario(
            usuario="slug_instructor",
            acceso=b"slugpass123",
            nombre="Slug",
            apellido="Instructor",
            correo_electronico="slug@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        # First MasterClass
        masterclass1 = MasterClass(
            title="First MasterClass",
            slug="unique-slug",
            description_public="First masterclass with this slug",
            date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/first",
            instructor_id="slug_instructor",
        )
        database.session.add(masterclass1)
        database.session.commit()

        # Second MasterClass with same slug should fail
        masterclass2 = MasterClass(
            title="Second MasterClass",
            slug="unique-slug",
            description_public="Second masterclass with same slug",
            date=date.today() + timedelta(days=14),
            start_time=time(14, 0),
            end_time=time(16, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/second",
            instructor_id="slug_instructor",
        )
        database.session.add(masterclass2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            database.session.commit()

    def test_masterclass_required_fields(self, app_context):
        """Test that required fields are enforced."""
        instructor = Usuario(
            usuario="required_instructor",
            acceso=b"requiredpass123",
            nombre="Required",
            apellido="Instructor",
            correo_electronico="required@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        # MasterClass without title should fail
        with pytest.raises(Exception):
            masterclass = MasterClass(
                slug="no-title",
                description_public="No title masterclass",
                date=date.today() + timedelta(days=7),
                start_time=time(10, 0),
                end_time=time(12, 0),
                platform_name="Zoom",
                platform_url="https://zoom.us/no-title",
                instructor_id="required_instructor",
            )
            database.session.add(masterclass)
            database.session.commit()

    def test_masterclass_time_validation(self, app_context):
        """Test logical time validation (start before end)."""
        instructor = Usuario(
            usuario="time_instructor",
            acceso=b"timepass123",
            nombre="Time",
            apellido="Instructor",
            correo_electronico="time@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        # Valid time range
        valid_masterclass = MasterClass(
            title="Valid Time MasterClass",
            slug="valid-time",
            description_public="Valid time range",
            date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/valid-time",
            instructor_id="time_instructor",
        )
        database.session.add(valid_masterclass)
        database.session.commit()
        
        # This should work fine - database doesn't enforce time logic
        # Time validation would be handled at the application level
        assert valid_masterclass.start_time < valid_masterclass.end_time


class TestMasterClassDiscountSystem:
    """Test MasterClass early discount functionality (though currently free)."""

    def test_early_discount_configuration(self, app_context):
        """Test early discount configuration (for future use)."""
        instructor = Usuario(
            usuario="discount_instructor",
            acceso=b"discountpass123",
            nombre="Discount",
            apellido="Instructor",
            correo_electronico="discount@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        # MasterClass with early discount configuration
        discount_masterclass = MasterClass(
            title="Discount MasterClass",
            slug="discount-masterclass",
            description_public="MasterClass with early discount",
            date=date.today() + timedelta(days=30),
            start_time=time(10, 0),
            end_time=time(12, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/discount",
            instructor_id="discount_instructor",
            is_paid=True,
            price=Decimal("100.00"),
            early_discount=Decimal("20.00"),  # 20% discount
            discount_deadline=datetime.now() + timedelta(days=14),
        )
        database.session.add(discount_masterclass)
        database.session.commit()
        
        # Verify discount configuration
        retrieved = database.session.execute(
            database.select(MasterClass).filter_by(slug="discount-masterclass")
        ).scalar_one()
        
        assert retrieved.early_discount == Decimal("20.00")
        assert retrieved.discount_deadline is not None
        
        # Even with discount configuration, effective price is still 0
        assert retrieved.get_effective_price() == 0


class TestMasterClassRelationships:
    """Test MasterClass relationships with other models."""

    def test_masterclass_instructor_relationship(self, app_context):
        """Test MasterClass relationship with instructor."""
        instructor = Usuario(
            usuario="rel_instructor",
            acceso=b"relpass123",
            nombre="Relationship",
            apellido="Instructor",
            correo_electronico="rel@instructor.com",
            tipo="instructor",
            activo=True,
        )
        database.session.add(instructor)
        database.session.commit()

        masterclass = MasterClass(
            title="Relationship Test",
            slug="relationship-test",
            description_public="Testing relationships",
            date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/rel",
            instructor_id="rel_instructor",
        )
        database.session.add(masterclass)
        database.session.commit()
        
        # Test instructor relationship
        retrieved = database.session.execute(
            database.select(MasterClass).filter_by(slug="relationship-test")
        ).scalar_one()
        
        assert retrieved.instructor is not None
        assert retrieved.instructor.usuario == "rel_instructor"
        assert retrieved.instructor.nombre == "Relationship"

    def test_masterclass_enrollments_relationship(self, app_context):
        """Test MasterClass relationship with enrollments."""
        instructor = Usuario(
            usuario="enroll_rel_instructor",
            acceso=b"enrollrelpass123",
            nombre="EnrollRel",
            apellido="Instructor",
            correo_electronico="enrollrel@instructor.com",
            tipo="instructor",
            activo=True,
        )
        
        student1 = Usuario(
            usuario="student1",
            acceso=b"student1pass",
            nombre="Student",
            apellido="One",
            correo_electronico="student1@test.com",
            tipo="user",
            activo=True,
        )
        
        student2 = Usuario(
            usuario="student2",
            acceso=b"student2pass",
            nombre="Student",
            apellido="Two",
            correo_electronico="student2@test.com",
            tipo="user",
            activo=True,
        )
        
        database.session.add_all([instructor, student1, student2])
        database.session.commit()

        masterclass = MasterClass(
            title="Enrollment Relationship Test",
            slug="enrollment-rel-test",
            description_public="Testing enrollment relationships",
            date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            platform_name="Zoom",
            platform_url="https://zoom.us/enrollrel",
            instructor_id="enroll_rel_instructor",
        )
        database.session.add(masterclass)
        database.session.commit()

        # Create enrollments
        enrollment1 = MasterClassEnrollment(
            master_class_id=masterclass.id,
            user_id="student1",
            is_confirmed=True,
        )
        
        enrollment2 = MasterClassEnrollment(
            master_class_id=masterclass.id,
            user_id="student2",
            is_confirmed=False,
        )
        
        database.session.add_all([enrollment1, enrollment2])
        database.session.commit()
        
        # Test enrollments relationship
        retrieved = database.session.execute(
            database.select(MasterClass).filter_by(slug="enrollment-rel-test")
        ).scalar_one()
        
        assert len(retrieved.enrollments) == 2
        confirmed_enrollments = [e for e in retrieved.enrollments if e.is_confirmed]
        assert len(confirmed_enrollments) == 1