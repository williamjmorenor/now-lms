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

"""Test misc utilities and helper functions."""

import pytest
from unittest.mock import patch, MagicMock
from now_lms.misc import check_generate_pdf, ESTILO_ALERTAS, ICONOS_ALERTAS, ESTILOS_ALERTAS


class TestMiscUtilities:
    """Test miscellaneous utilities."""

    def test_alert_styles_constants(self):
        """Test alert styles constants are properly defined."""
        # Test that icon constants exist
        assert "success" in ICONOS_ALERTAS
        assert "info" in ICONOS_ALERTAS
        assert "error" in ICONOS_ALERTAS
        assert "warning" in ICONOS_ALERTAS
        
        # Test that style classes exist
        assert "success" in ESTILOS_ALERTAS
        assert "info" in ESTILOS_ALERTAS
        assert "error" in ESTILOS_ALERTAS
        assert "warning" in ESTILOS_ALERTAS
        
        # Test the combined style object
        assert hasattr(ESTILO_ALERTAS, 'icono')
        assert hasattr(ESTILO_ALERTAS, 'clase')
        assert ESTILO_ALERTAS.icono == ICONOS_ALERTAS
        assert ESTILO_ALERTAS.clase == ESTILOS_ALERTAS

    def test_alert_styles_values(self):
        """Test that alert styles have expected values."""
        # Test icon values (should be Bootstrap icons)
        assert "bi " in ICONOS_ALERTAS["success"]
        assert "bi " in ICONOS_ALERTAS["info"]
        assert "bi " in ICONOS_ALERTAS["error"]
        assert "bi " in ICONOS_ALERTAS["warning"]
        
        # Test CSS class values (should be Bootstrap alert classes)
        assert "alert" in ESTILOS_ALERTAS["success"]
        assert "alert" in ESTILOS_ALERTAS["info"]
        assert "alert" in ESTILOS_ALERTAS["error"]
        assert "alert" in ESTILOS_ALERTAS["warning"]

    @patch('now_lms.misc.getcwd')
    @patch('now_lms.misc.HTML')
    @patch('now_lms.misc.CSS')
    @patch('jinja2.Environment')
    @patch('now_lms.misc.database')
    def test_check_generate_pdf_success(self, mock_database, mock_env, mock_css, mock_html, mock_getcwd):
        """Test successful PDF generation."""
        # Mock database query
        mock_cert = MagicMock()
        mock_cert.html = "<html><body>Test Certificate</body></html>"
        mock_cert.css = "body { font-family: Arial; }"
        
        mock_database.session.execute.return_value.first.return_value = (mock_cert,)
        
        # Mock template rendering
        mock_template = MagicMock()
        mock_template.render.return_value = "<html><body>Rendered Certificate</body></html>"
        mock_env.return_value.from_string.return_value = mock_template
        
        # Mock HTML and CSS objects
        mock_html_obj = MagicMock()
        mock_html.return_value = mock_html_obj
        mock_css_obj = MagicMock()
        mock_css.return_value = mock_css_obj
        
        # Mock getcwd
        mock_getcwd.return_value = "/test/dir"
        
        # Call the function
        check_generate_pdf()
        
        # Verify calls
        mock_database.session.execute.assert_called_once()
        mock_env.assert_called_once()
        mock_template.render.assert_called_once()
        mock_html.assert_called_once()
        mock_css.assert_called_once()
        mock_html_obj.write_pdf.assert_called_once_with("/test/dir/test.pdf", stylesheets=[mock_css_obj])

    @patch('now_lms.misc.database')
    def test_check_generate_pdf_no_certificate(self, mock_database):
        """Test PDF generation when no certificate is found."""
        # Mock database query returning None
        mock_database.session.execute.return_value.first.return_value = None
        
        # Should raise an exception when trying to access cert[0]
        with pytest.raises((AttributeError, TypeError)):
            check_generate_pdf()

    @patch('jinja2.Environment')
    @patch('now_lms.misc.HTML')
    @patch('now_lms.misc.database')
    def test_check_generate_pdf_template_error(self, mock_database, mock_html, mock_env):
        """Test PDF generation with template rendering error."""
        # Mock database query
        mock_cert = MagicMock()
        mock_cert.html = "<html><body>Test Certificate</body></html>"
        mock_cert.css = "body { font-family: Arial; }"
        
        mock_database.session.execute.return_value.first.return_value = (mock_cert,)
        
        # Mock template with rendering error
        mock_template = MagicMock()
        mock_template.render.side_effect = Exception("Template error")
        mock_env.return_value.from_string.return_value = mock_template
        
        # Should raise exception during template rendering
        with pytest.raises(Exception):
            check_generate_pdf()

    @patch('now_lms.misc.getcwd')
    @patch('jinja2.Environment')
    @patch('now_lms.misc.CSS')
    @patch('now_lms.misc.HTML')
    @patch('now_lms.misc.database')
    def test_check_generate_pdf_write_error(self, mock_database, mock_html, mock_css, mock_env, mock_getcwd):
        """Test PDF generation with file write error."""
        # Mock database query
        mock_cert = MagicMock()
        mock_cert.html = "<html><body>Test Certificate</body></html>"
        mock_cert.css = "body { font-family: Arial; }"
        
        mock_database.session.execute.return_value.first.return_value = (mock_cert,)
        
        # Mock template rendering
        mock_template = MagicMock()
        mock_template.render.return_value = "<html><body>Rendered Certificate</body></html>"
        mock_env.return_value.from_string.return_value = mock_template
        
        # Mock HTML object with write error
        mock_html_obj = MagicMock()
        mock_html_obj.write_pdf.side_effect = Exception("Write error")
        mock_html.return_value = mock_html_obj
        
        mock_css_obj = MagicMock()
        mock_css.return_value = mock_css_obj
        
        mock_getcwd.return_value = "/test/dir"
        
        # Should raise exception during PDF writing
        with pytest.raises(Exception):
            check_generate_pdf()

    def test_alert_styles_completeness(self):
        """Test that all alert types have both icons and styles defined."""
        alert_types = ["success", "info", "error", "warning"]
        
        for alert_type in alert_types:
            assert alert_type in ICONOS_ALERTAS, f"Missing icon for {alert_type}"
            assert alert_type in ESTILOS_ALERTAS, f"Missing style for {alert_type}"
            
            # Ensure values are not empty
            assert ICONOS_ALERTAS[alert_type], f"Empty icon for {alert_type}"
            assert ESTILOS_ALERTAS[alert_type], f"Empty style for {alert_type}"


class TestMiscEdgeCases:
    """Test edge cases and error conditions."""

    def test_estilo_alertas_object_properties(self):
        """Test the EstiloAlterta named tuple properties."""
        # Test that we can access properties correctly
        icono_success = ESTILO_ALERTAS.icono["success"]
        clase_success = ESTILO_ALERTAS.clase["success"]
        
        assert icono_success == ICONOS_ALERTAS["success"]
        assert clase_success == ESTILOS_ALERTAS["success"]

    def test_alert_constants_immutability(self):
        """Test that alert constants behave as expected."""
        # These should be dictionaries
        assert isinstance(ICONOS_ALERTAS, dict)
        assert isinstance(ESTILOS_ALERTAS, dict)
        
        # Should have the expected keys
        expected_keys = {"success", "info", "error", "warning"}
        assert set(ICONOS_ALERTAS.keys()) == expected_keys
        assert set(ESTILOS_ALERTAS.keys()) == expected_keys