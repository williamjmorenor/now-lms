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

"""Test i18n utilities."""

import pytest
from unittest.mock import patch, MagicMock

from now_lms.i18n import (
    get_configuracion,
    get_locale,
    get_timezone,
    invalidate_configuracion_cache,
    _get_locales,
    _get_timezone
)


class TestI18nUtilities:
    """Test internationalization utilities."""

    @patch('now_lms.i18n.database')
    def test_get_configuracion_exists(self, mock_database):
        """Test get_configuracion when configuration exists."""
        # Mock existing configuration
        mock_config = MagicMock()
        mock_config.lang = "es"
        mock_config.time_zone = "Europe/Madrid"
        mock_config.titulo = "Test Title"
        mock_config.descripcion = "Test Description"
        
        mock_database.session.execute.return_value.scalars.return_value.first.return_value = mock_config
        
        with patch('now_lms.i18n.cache') as mock_cache:
            # Mock cache decorator behavior
            mock_cache.cached.return_value = lambda func: func
            
            result = get_configuracion()
            assert result == mock_config
            assert result.lang == "es"
            assert result.time_zone == "Europe/Madrid"

    @patch('now_lms.i18n.database')
    @patch('now_lms.i18n.Configuracion')
    def test_get_configuracion_fallback(self, mock_configuracion_class, mock_database):
        """Test get_configuracion fallback when no configuration exists."""
        # Mock no configuration found
        mock_database.session.execute.return_value.scalars.return_value.first.return_value = None
        
        # Mock the fallback configuration creation
        mock_fallback = MagicMock()
        mock_fallback.lang = "en"
        mock_fallback.time_zone = "UTC"
        mock_configuracion_class.return_value = mock_fallback
        
        with patch('now_lms.i18n.cache') as mock_cache:
            mock_cache.cached.return_value = lambda func: func
            
            result = get_configuracion()
            
            # Should create fallback configuration
            mock_configuracion_class.assert_called_once_with(
                lang="en", 
                time_zone="UTC", 
                titulo="Título por defecto", 
                descripcion="Descripción"
            )
            assert result == mock_fallback

    @patch('flask.g')
    def test_get_locale_from_g_config(self, mock_g):
        """Test get_locale when configuration is in Flask g."""
        mock_config = MagicMock()
        mock_config.lang = "es"
        mock_g.configuracion = mock_config
        
        result = get_locale()
        assert result == "es"

    @patch('flask.g')
    @patch('flask.request')
    def test_get_locale_fallback_to_request(self, mock_request, mock_g):
        """Test get_locale fallback to request accept languages."""
        # Mock no configuration in g
        mock_g.configuracion = None
        
        # Mock request accept languages
        mock_request.accept_languages.best_match.return_value = "en"
        
        result = get_locale()
        assert result == "en"
        mock_request.accept_languages.best_match.assert_called_once_with(["es", "en"])

    @patch('flask.g')
    @patch('flask.request')
    def test_get_locale_ultimate_fallback(self, mock_request, mock_g):
        """Test get_locale ultimate fallback when no preferred language."""
        # Mock no configuration in g
        mock_g.configuracion = None
        
        # Mock request accept languages returning None
        mock_request.accept_languages.best_match.return_value = None
        
        result = get_locale()
        assert result == "en"

    @patch('flask.g')
    def test_get_locale_no_lang_attribute(self, mock_g):
        """Test get_locale when config exists but has no lang attribute."""
        mock_config = MagicMock()
        # Mock config without lang attribute
        mock_config.lang = None
        mock_g.configuracion = mock_config
        
        with patch('flask.request') as mock_request:
            mock_request.accept_languages.best_match.return_value = "en"
            result = get_locale()
            assert result == "en"

    @patch('flask.g')
    def test_get_timezone_from_g_config(self, mock_g):
        """Test get_timezone when configuration is in Flask g."""
        mock_config = MagicMock()
        mock_config.time_zone = "Europe/Madrid"
        mock_g.configuracion = mock_config
        
        result = get_timezone()
        assert result == "Europe/Madrid"

    @patch('flask.g')
    def test_get_timezone_fallback(self, mock_g):
        """Test get_timezone fallback when no configuration."""
        mock_g.configuracion = None
        
        result = get_timezone()
        assert result == "UTC"

    @patch('flask.g')
    def test_get_timezone_no_attribute(self, mock_g):
        """Test get_timezone when config exists but has no time_zone attribute."""
        mock_config = MagicMock()
        mock_config.time_zone = None
        mock_g.configuracion = mock_config
        
        result = get_timezone()
        assert result == "UTC"

    @patch('now_lms.i18n.cache')
    @patch('now_lms.i18n.log')
    def test_invalidate_configuracion_cache(self, mock_log, mock_cache):
        """Test invalidate_configuracion_cache function."""
        invalidate_configuracion_cache()
        
        mock_cache.delete.assert_called_once_with("configuracion_global")
        mock_log.trace.assert_called_once_with("Cache de configuración invalidada")

    def test_legacy_get_locales(self):
        """Test legacy _get_locales function."""
        with patch('now_lms.i18n.get_locale') as mock_get_locale:
            mock_get_locale.return_value = "es"
            
            result = _get_locales()
            assert result == "es"
            mock_get_locale.assert_called_once()

    def test_legacy_get_timezone(self):
        """Test legacy _get_timezone function."""
        with patch('now_lms.i18n.get_timezone') as mock_get_timezone:
            mock_get_timezone.return_value = "Europe/Madrid"
            
            result = _get_timezone()
            assert result == "Europe/Madrid"
            mock_get_timezone.assert_called_once()


class TestI18nEdgeCases:
    """Test edge cases for i18n utilities."""

    @patch('flask.g')
    def test_get_locale_hasattr_false(self, mock_g):
        """Test get_locale when g has no configuracion attribute."""
        # Mock g without configuracion attribute
        del mock_g.configuracion
        
        with patch('flask.request') as mock_request:
            mock_request.accept_languages.best_match.return_value = "es"
            result = get_locale()
            assert result == "es"

    @patch('flask.g')
    def test_get_timezone_hasattr_false(self, mock_g):
        """Test get_timezone when g has no configuracion attribute."""
        # Mock g without configuracion attribute
        del mock_g.configuracion
        
        result = get_timezone()
        assert result == "UTC"

    @patch('flask.g')
    def test_get_locale_config_none(self, mock_g):
        """Test get_locale when g.configuracion is explicitly None."""
        mock_g.configuracion = None
        
        with patch('flask.request') as mock_request:
            mock_request.accept_languages.best_match.return_value = "fr"
            result = get_locale()
            assert result == "fr"

    @patch('flask.g')
    def test_get_timezone_config_none(self, mock_g):
        """Test get_timezone when g.configuracion is explicitly None."""
        mock_g.configuracion = None
        
        result = get_timezone()
        assert result == "UTC"

    @patch('flask.g')
    def test_get_locale_getattr_with_default(self, mock_g):
        """Test get_locale getattr behavior with default value."""
        mock_config = MagicMock()
        # Simulate getattr returning default when attribute doesn't exist
        mock_config.lang = "pt"
        mock_g.configuracion = mock_config
        
        result = get_locale()
        assert result == "pt"

    @patch('flask.g')
    def test_get_timezone_getattr_with_default(self, mock_g):
        """Test get_timezone getattr behavior with default value."""
        mock_config = MagicMock()
        # Simulate getattr returning default when attribute doesn't exist
        mock_config.time_zone = "America/New_York"
        mock_g.configuracion = mock_config
        
        result = get_timezone()
        assert result == "America/New_York"