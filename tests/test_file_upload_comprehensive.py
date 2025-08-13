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

"""Comprehensive tests for file upload functionality."""

import io
import pytest
from unittest.mock import patch, MagicMock
from flask import url_for
from werkzeug.datastructures import FileStorage

from now_lms.db import (
    Curso,
    CursoSeccion,
    CursoRecurso,
    Usuario,
    DocenteCurso,
    database,
    select,
)


class TestFileUploadFunctionality:
    """Test file upload functionality across different resource types."""
    
    @pytest.fixture
    def instructor_user(self, full_db_setup):
        """Create and login an instructor user."""
        from now_lms.auth import proteger_passwd
        
        with full_db_setup.app_context():
            instructor = Usuario(
                usuario="test_instructor",
                nombre="Test",
                apellido="Instructor",
                correo_electronico="instructor@test.com",
                tipo="instructor",
                activo=True,
                correo_electronico_verificado=True,
                acceso=proteger_passwd("password123"),
            )
            database.session.add(instructor)
            database.session.commit()
            return instructor
    
    @pytest.fixture
    def test_course(self, full_db_setup, instructor_user):
        """Create a test course."""
        with full_db_setup.app_context():
            course = Curso(
                codigo="TESTUPLOAD001",
                nombre="Test Upload Course",
                descripcion_corta="Course for testing uploads",
                descripcion="A course for testing file upload functionality",
                estado="draft",
                modalidad="self_paced",
                pagado=False,
                certificado=False,
                creado_por="test_instructor",  # Use string instead of object
            )
            database.session.add(course)
            
            # Assign instructor to course
            assignment = DocenteCurso(
                curso=course.codigo,
                usuario="test_instructor",  # Use string instead of object
                vigente=True,
            )
            database.session.add(assignment)
            
            database.session.commit()
            return course
    
    @pytest.fixture
    def test_section(self, full_db_setup, test_course):
        """Create a test section."""
        with full_db_setup.app_context():
            section = CursoSeccion(
                curso="TESTUPLOAD001",  # Use string instead of object
                nombre="Test Section",
                descripcion="Test section for uploads",
                indice=1,
                estado=True,
            )
            database.session.add(section)
            database.session.commit()
            return section
    
    @pytest.fixture
    def authenticated_client(self, full_db_setup, instructor_user):
        """Get authenticated client for instructor."""
        client = full_db_setup.test_client()
        
        # Login the instructor using the correct endpoint
        with full_db_setup.app_context():
            login_data = {
                'usuario': 'test_instructor',
                'acceso': 'password123'
            }
            response = client.post('/user/login', data=login_data, follow_redirects=True)
            assert response.status_code == 200
        
        return client
    
    def create_test_file(self, filename, content=b"test content", content_type="text/plain"):
        """Helper to create test files."""
        return FileStorage(
            stream=io.BytesIO(content),
            filename=filename,
            content_type=content_type
        )
    
    def create_pdf_file(self, filename="test.pdf"):
        """Helper to create a minimal PDF file."""
        # Minimal PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f 
0000000010 00000 n 
0000000079 00000 n 
0000000173 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
301
%%EOF"""
        return FileStorage(
            stream=io.BytesIO(pdf_content),
            filename=filename,
            content_type="application/pdf"
        )
    
    def create_image_file(self, filename="test.jpg"):
        """Helper to create a minimal image file."""
        # Minimal JPEG content (1x1 pixel)
        jpeg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
        return FileStorage(
            stream=io.BytesIO(jpeg_content),
            filename=filename,
            content_type="image/jpeg"
        )

    def create_audio_file(self, filename="test.ogg"):
        """Helper to create a minimal audio file."""
        # Minimal OGG Vorbis header
        ogg_content = b'OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x01vorbis\x00\x00\x00\x00\x02D\xac\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\xb8\x01'
        return FileStorage(
            stream=io.BytesIO(ogg_content),
            filename=filename,
            content_type="audio/ogg"
        )


class TestCourseLogoUpload(TestFileUploadFunctionality):
    """Test course logo upload functionality."""
    
    @patch('now_lms.vistas.courses.images')
    def test_course_creation_with_logo_upload_success(self, mock_images, authenticated_client, full_db_setup):
        """Test successful course creation with logo upload."""
        mock_images.save.return_value = "test_logo.jpg"
        mock_images.name = "images"
        
        with full_db_setup.app_context():
            course_data = {
                'codigo': 'LOGOCOURSE001',
                'nombre': 'Course with Logo',
                'descripcion_corta': 'Short description',
                'descripcion': 'Long description',
                'nivel': '0',
                'duracion': '10',
                'modalidad': 'self_paced',
                'pagado': False,
                'certificado': False,
                'plantilla_certificado': '',
            }
            
            image_file = self.create_image_file("course_logo.jpg")
            course_data['logo'] = image_file
            
            response = authenticated_client.post(
                '/course/new_curse',
                data=course_data,
                content_type='multipart/form-data',
                follow_redirects=True
            )
            
            # Verify successful response
            assert response.status_code == 200
            
            # Verify the upload was attempted (this should now work since we see "Course Logo saved")
            mock_images.save.assert_called_once()
            
            # Verify the course was created with logo flag
            curso = database.session.execute(
                database.select(Curso).filter_by(codigo='LOGOCOURSE001')
            ).scalar_one_or_none()
            
            assert curso is not None
            assert curso.nombre == 'Course with Logo'
            assert curso.portada is True  # Logo upload should set this to True
    
    @patch('now_lms.vistas.courses.images')
    def test_course_logo_upload_failure_handling(self, mock_images, authenticated_client, full_db_setup):
        """Test course logo upload failure handling."""
        from flask_uploads import UploadNotAllowed
        mock_images.save.side_effect = UploadNotAllowed("Invalid file type")
        mock_images.name = "images"
        
        with full_db_setup.app_context():
            course_data = {
                'codigo': 'LOGOFAIL001',
                'nombre': 'Course Logo Fail',
                'descripcion_corta': 'Short description',
                'descripcion': 'Long description',
                'nivel': '0',
                'duracion': '10',
                'modalidad': 'self_paced',
                'pagado': False,
                'certificado': False,
                'plantilla_certificado': '',
            }
            
            # Invalid file type
            invalid_file = self.create_test_file("invalid.txt", content_type="text/plain")
            course_data['logo'] = invalid_file
            
            with patch('now_lms.vistas.courses.current_user') as mock_user:
                mock_user.usuario = "test_instructor"
                
                response = authenticated_client.post(
                    '/course/new_curse',
                    data=course_data,
                    content_type='multipart/form-data',
                    follow_redirects=True
                )
                
                # Should handle the error gracefully
                assert response.status_code == 200


class TestPDFResourceUpload(TestFileUploadFunctionality):
    """Test PDF resource upload functionality."""
    
    @patch('now_lms.vistas.courses.files')
    def test_pdf_resource_upload_success(self, mock_files, authenticated_client, full_db_setup):
        """Test successful PDF resource upload."""
        mock_files.save.return_value = "test_document.pdf"
        mock_files.name = "files"
        
        with full_db_setup.app_context():
            # Create course and section in the same context as the test
            course = Curso(
                codigo="PDFTEST001",
                nombre="PDF Test Course",
                descripcion_corta="Course for testing PDF uploads",
                descripcion="A course for testing PDF upload functionality",
                estado="draft",
                modalidad="self_paced",
                pagado=False,
                certificado=False,
                creado_por="test_instructor",
            )
            database.session.add(course)
            
            # Assign instructor to course
            assignment = DocenteCurso(
                curso=course.codigo,
                usuario="test_instructor",
                vigente=True,
            )
            database.session.add(assignment)
            
            # Create section
            section = CursoSeccion(
                curso=course.codigo,
                nombre="Test PDF Section",
                descripcion="Test section for PDF uploads",
                indice=1,
                estado=True,
            )
            database.session.add(section)
            database.session.commit()
            
            pdf_data = {
                'nombre': 'Test PDF Resource',
                'descripcion': 'A test PDF document',
                'requerido': 'required',
            }
            
            pdf_file = self.create_pdf_file("document.pdf")
            pdf_data['pdf'] = pdf_file
            
            response = authenticated_client.post(
                f'/course/{course.codigo}/{section.id}/pdf/new',
                data=pdf_data,
                content_type='multipart/form-data',
                follow_redirects=True
            )
            
            # Verify the upload was attempted
            mock_files.save.assert_called_once()
            assert response.status_code == 200
            
            # Verify resource was created
            resource = database.session.execute(
                select(CursoRecurso).filter_by(
                    curso=course.codigo,
                    seccion=section.id,
                    tipo="pdf"
                )
            ).scalar_one_or_none()
            
            assert resource is not None
            assert resource.nombre == 'Test PDF Resource'
            assert resource.doc == "test_document.pdf"
    
    def test_pdf_resource_upload_no_file(self, authenticated_client, full_db_setup, test_course, test_section):
        """Test PDF resource upload without file."""
        with full_db_setup.app_context():
            pdf_data = {
                'nombre': 'Test PDF Without File',
                'descripcion': 'A test PDF without file',
                'requerido': 'required',
            }
            
            response = authenticated_client.post(
                f'/course/{test_course.codigo}/{test_section.id}/pdf/new',
                data=pdf_data,
                content_type='multipart/form-data'
            )
            
            # Should return the form page since no file was uploaded
            assert response.status_code == 200
            assert b"nuevo_recurso_pdf.html" in response.data or "PDF" in response.get_data(as_text=True)
    
    @patch('now_lms.vistas.courses.files')
    def test_pdf_resource_edit_with_new_file(self, mock_files, authenticated_client, full_db_setup, test_course, test_section):
        """Test editing PDF resource with new file upload."""
        mock_files.save.return_value = "updated_document.pdf"
        mock_files.name = "files"
        
        with full_db_setup.app_context():
            # Create initial resource
            resource = CursoRecurso(
                curso=test_course.codigo,
                seccion=test_section.id,
                tipo="pdf",
                nombre="Original PDF",
                descripcion="Original description",
                requerido="required",
                indice=1,
                doc="original.pdf",
                base_doc_url="files",
            )
            database.session.add(resource)
            database.session.commit()
            
            # Update with new file
            update_data = {
                'nombre': 'Updated PDF Resource',
                'descripcion': 'Updated description',
                'requerido': 'optional',
            }
            
            new_pdf = self.create_pdf_file("new_document.pdf")
            update_data['pdf'] = new_pdf
            
            with patch('now_lms.vistas.courses.current_user') as mock_user:
                mock_user.usuario = "test_instructor"
                
                response = authenticated_client.post(
                    f'/course/{test_course.codigo}/{test_section.id}/pdf/{resource.id}/edit',
                    data=update_data,
                    content_type='multipart/form-data',
                    follow_redirects=True
                )
                
                mock_files.save.assert_called_once()
                assert response.status_code == 200
                
                # Verify resource was updated
                updated_resource = database.session.get(CursoRecurso, resource.id)
                assert updated_resource.nombre == 'Updated PDF Resource'
                assert updated_resource.doc == "updated_document.pdf"


class TestImageResourceUpload(TestFileUploadFunctionality):
    """Test image resource upload functionality."""
    
    @patch('now_lms.vistas.courses.images')
    def test_image_resource_upload_success(self, mock_images, authenticated_client, full_db_setup, test_course, test_section):
        """Test successful image resource upload."""
        mock_images.save.return_value = "test_image.jpg"
        mock_images.name = "images"
        
        with full_db_setup.app_context():
            image_data = {
                'nombre': 'Test Image Resource',
                'descripcion': 'A test image',
                'requerido': 'required',
            }
            
            image_file = self.create_image_file("test_image.jpg")
            image_data['img'] = image_file
            
            with patch('now_lms.vistas.courses.current_user') as mock_user:
                mock_user.usuario = "test_instructor"
                
                response = authenticated_client.post(
                    f'/course/{test_course.codigo}/{test_section.id}/img/new',
                    data=image_data,
                    content_type='multipart/form-data',
                    follow_redirects=True
                )
                
                mock_images.save.assert_called_once()
                assert response.status_code == 200
                
                # Verify resource was created
                resource = database.session.execute(
                    select(CursoRecurso).filter_by(
                        curso=test_course.codigo,
                        seccion=test_section.id,
                        tipo="img"
                    )
                ).scalar_one_or_none()
                
                assert resource is not None
                assert resource.nombre == 'Test Image Resource'
                assert resource.doc == "test_image.jpg"
    
    def test_image_resource_upload_no_file(self, authenticated_client, full_db_setup, test_course, test_section):
        """Test image resource upload without file."""
        with full_db_setup.app_context():
            image_data = {
                'nombre': 'Test Image Without File',
                'descripcion': 'A test image without file',
                'requerido': 'required',
            }
            
            response = authenticated_client.post(
                f'/course/{test_course.codigo}/{test_section.id}/img/new',
                data=image_data,
                content_type='multipart/form-data'
            )
            
            # Should return the form page since no file was uploaded
            assert response.status_code == 200


class TestAudioResourceUpload(TestFileUploadFunctionality):
    """Test audio resource upload functionality."""
    
    @patch('now_lms.vistas.courses.audio')
    def test_audio_resource_upload_success(self, mock_audio, authenticated_client, full_db_setup, test_course, test_section):
        """Test successful audio resource upload."""
        mock_audio.save.return_value = "test_audio.ogg"
        mock_audio.name = "audio"
        
        with full_db_setup.app_context():
            audio_data = {
                'nombre': 'Test Audio Resource',
                'descripcion': 'A test audio file',
                'requerido': 'required',
            }
            
            audio_file = self.create_audio_file("test_audio.ogg")
            audio_data['audio'] = audio_file
            
            with patch('now_lms.vistas.courses.current_user') as mock_user:
                mock_user.usuario = "test_instructor"
                
                response = authenticated_client.post(
                    f'/course/{test_course.codigo}/{test_section.id}/audio/new',
                    data=audio_data,
                    content_type='multipart/form-data',
                    follow_redirects=True
                )
                
                mock_audio.save.assert_called_once()
                assert response.status_code == 200
                
                # Verify resource was created
                resource = database.session.execute(
                    select(CursoRecurso).filter_by(
                        curso=test_course.codigo,
                        seccion=test_section.id,
                        tipo="mp3"
                    )
                ).scalar_one_or_none()
                
                assert resource is not None
                assert resource.nombre == 'Test Audio Resource'
                assert resource.doc == "test_audio.ogg"
    
    def test_audio_resource_upload_no_file(self, authenticated_client, full_db_setup, test_course, test_section):
        """Test audio resource upload without file."""
        with full_db_setup.app_context():
            audio_data = {
                'nombre': 'Test Audio Without File',
                'descripcion': 'A test audio without file',
                'requerido': 'required',
            }
            
            response = authenticated_client.post(
                f'/course/{test_course.codigo}/{test_section.id}/audio/new',
                data=audio_data,
                content_type='multipart/form-data'
            )
            
            # Should return the form page since no file was uploaded
            assert response.status_code == 200


class TestFileUploadErrorCases(TestFileUploadFunctionality):
    """Test error cases and edge conditions for file uploads."""
    
    def test_upload_without_authentication(self, full_db_setup, test_course, test_section):
        """Test that file upload requires authentication."""
        client = full_db_setup.test_client()
        
        with full_db_setup.app_context():
            pdf_data = {
                'nombre': 'Unauthorized PDF',
                'descripcion': 'This should fail',
                'requerido': 'required',
                'pdf': self.create_pdf_file("unauthorized.pdf")
            }
            
            response = client.post(
                f'/course/{test_course.codigo}/{test_section.id}/pdf/new',
                data=pdf_data,
                content_type='multipart/form-data'
            )
            
            # Should redirect to login or return 401/403
            assert response.status_code in [302, 401, 403]
    
    @patch('now_lms.vistas.courses.files')
    def test_upload_with_database_error(self, mock_files, authenticated_client, full_db_setup, test_course, test_section):
        """Test file upload with database error."""
        from sqlalchemy.exc import OperationalError
        
        mock_files.save.return_value = "test_document.pdf"
        mock_files.name = "files"
        
        with full_db_setup.app_context():
            pdf_data = {
                'nombre': 'PDF with DB Error',
                'descripcion': 'This will cause a DB error',
                'requerido': 'required',
            }
            
            pdf_file = self.create_pdf_file("db_error.pdf")
            pdf_data['pdf'] = pdf_file
            
            with patch('now_lms.vistas.courses.database.session.commit') as mock_commit:
                mock_commit.side_effect = OperationalError("DB Error", None, None)
                
                with patch('now_lms.vistas.courses.current_user') as mock_user:
                    mock_user.usuario = "test_instructor"
                    
                    response = authenticated_client.post(
                        f'/course/{test_course.codigo}/{test_section.id}/pdf/new',
                        data=pdf_data,
                        content_type='multipart/form-data',
                        follow_redirects=True
                    )
                    
                    # Should handle the error gracefully
                    assert response.status_code == 200
    
    def test_upload_to_nonexistent_course(self, authenticated_client, full_db_setup):
        """Test upload to a course that doesn't exist."""
        with full_db_setup.app_context():
            pdf_data = {
                'nombre': 'PDF for Nonexistent Course',
                'descripcion': 'This should fail',
                'requerido': 'required',
                'pdf': self.create_pdf_file("nonexistent.pdf")
            }
            
            response = authenticated_client.post(
                '/course/NONEXISTENT/999/pdf/new',
                data=pdf_data,
                content_type='multipart/form-data'
            )
            
            # Should return an error (404 or other)
            assert response.status_code in [404, 500]
    
    def test_upload_with_empty_filename(self, authenticated_client, full_db_setup, test_course, test_section):
        """Test upload with empty filename."""
        with full_db_setup.app_context():
            pdf_data = {
                'nombre': 'PDF with Empty Filename',
                'descripcion': 'Testing empty filename',
                'requerido': 'required',
            }
            
            # Create file with empty filename
            empty_file = FileStorage(
                stream=io.BytesIO(b"test content"),
                filename="",
                content_type="application/pdf"
            )
            pdf_data['pdf'] = empty_file
            
            response = authenticated_client.post(
                f'/course/{test_course.codigo}/{test_section.id}/pdf/new',
                data=pdf_data,
                content_type='multipart/form-data'
            )
            
            # Should handle empty filename gracefully
            assert response.status_code == 200


class TestFileServingAndAccess(TestFileUploadFunctionality):
    """Test file serving and access control."""
    
    def test_file_access_with_authentication(self, authenticated_client, full_db_setup, test_course, test_section):
        """Test file access with proper authentication."""
        with full_db_setup.app_context():
            # Create a resource with a file
            resource = CursoRecurso(
                curso=test_course.codigo,
                seccion=test_section.id,
                tipo="pdf",
                nombre="Test PDF",
                descripcion="Test description",
                requerido="required",
                indice=1,
                doc="test.pdf",
                base_doc_url="files",
                publico=True,
            )
            database.session.add(resource)
            database.session.commit()
            
            with patch('now_lms.vistas.courses.send_from_directory') as mock_send:
                mock_send.return_value = "file_content"
                
                response = authenticated_client.get(
                    f'/course/{test_course.codigo}/files/{resource.id}'
                )
                
                # File access should work for authenticated instructor
                assert response.status_code == 200
    
    def test_file_access_without_authentication(self, full_db_setup, test_course, test_section):
        """Test file access without authentication."""
        client = full_db_setup.test_client()
        
        with full_db_setup.app_context():
            # Create a private resource
            resource = CursoRecurso(
                curso=test_course.codigo,
                seccion=test_section.id,
                tipo="pdf",
                nombre="Private PDF",
                descripcion="Private description",
                requerido="required",
                indice=1,
                doc="private.pdf",
                base_doc_url="files",
                publico=False,
            )
            database.session.add(resource)
            database.session.commit()
            
            response = client.get(
                f'/course/{test_course.codigo}/files/{resource.id}'
            )
            
            # Should redirect to login
            assert response.status_code in [302, 401, 403]