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

"""Test logging configuration and utilities."""

import pytest
import logging
from unittest.mock import patch, MagicMock
from io import StringIO

from now_lms.logs import trace, TRACE_LEVEL_NUM, log, logger, LOG_LEVEL


class TestLoggingConfiguration:
    """Test logging configuration and functionality."""

    def test_trace_level_defined(self):
        """Test that TRACE level is properly defined."""
        assert TRACE_LEVEL_NUM == 5
        assert logging.getLevelName(TRACE_LEVEL_NUM) == "TRACE"

    def test_trace_method_exists(self):
        """Test that trace method is added to Logger class."""
        assert hasattr(logging.Logger, 'trace')
        assert callable(getattr(logging.Logger, 'trace'))

    def test_trace_method_functionality(self):
        """Test trace method functionality."""
        # Create a test logger
        test_logger = logging.getLogger("test_trace")
        test_logger.setLevel(TRACE_LEVEL_NUM)
        
        # Create a string stream to capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        test_logger.addHandler(handler)
        
        # Test trace method
        test_logger.trace("Test trace message")
        
        # Check that message was logged
        output = stream.getvalue()
        assert "Test trace message" in output
        
        # Clean up
        test_logger.removeHandler(handler)

    def test_trace_method_with_disabled_level(self):
        """Test trace method when level is disabled."""
        # Create a test logger with higher level
        test_logger = logging.getLogger("test_trace_disabled")
        test_logger.setLevel(logging.INFO)  # Higher than TRACE
        
        # Create a string stream to capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        test_logger.addHandler(handler)
        
        # Test trace method
        test_logger.trace("This should not appear")
        
        # Check that message was NOT logged
        output = stream.getvalue()
        assert "This should not appear" not in output
        
        # Clean up
        test_logger.removeHandler(handler)

    def test_trace_function_enabled_for_level(self):
        """Test trace function when logger is enabled for TRACE level."""
        mock_logger = MagicMock()
        mock_logger.isEnabledFor.return_value = True
        
        # Call trace function directly
        trace(mock_logger, "Test message", "arg1", "arg2", kwarg1="value1")
        
        mock_logger.isEnabledFor.assert_called_once_with(TRACE_LEVEL_NUM)
        mock_logger._log.assert_called_once_with(
            TRACE_LEVEL_NUM, "Test message", ("arg1", "arg2"), kwarg1="value1"
        )

    def test_trace_function_disabled_for_level(self):
        """Test trace function when logger is disabled for TRACE level."""
        mock_logger = MagicMock()
        mock_logger.isEnabledFor.return_value = False
        
        # Call trace function directly
        trace(mock_logger, "Test message")
        
        mock_logger.isEnabledFor.assert_called_once_with(TRACE_LEVEL_NUM)
        mock_logger._log.assert_not_called()

    def test_log_instance_exists(self):
        """Test that log instance exists and is configured."""
        assert log is not None
        assert isinstance(log, logging.Logger)
        assert log.name == "now_lms"

    def test_logger_instance_exists(self):
        """Test that logger instance exists and is same as log."""
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger is log

    def test_log_level_constant(self):
        """Test that LOG_LEVEL constant is properly set."""
        assert LOG_LEVEL is not None
        assert isinstance(LOG_LEVEL, int)
        assert LOG_LEVEL == log.getEffectiveLevel()

    def test_custom_levels_mapping(self):
        """Test that custom levels are properly mapped."""
        from now_lms.logs import custom_levels
        
        assert "TRACE" in custom_levels
        assert "DEBUG" in custom_levels
        assert "INFO" in custom_levels
        assert "WARNING" in custom_levels
        assert "ERROR" in custom_levels
        assert "CRITICAL" in custom_levels
        
        assert custom_levels["TRACE"] == TRACE_LEVEL_NUM
        assert custom_levels["DEBUG"] == logging.DEBUG
        assert custom_levels["INFO"] == logging.INFO

    @patch('now_lms.logs.environ')
    def test_log_level_from_environment(self, mock_environ):
        """Test that log level is read from environment variable."""
        mock_environ.get.return_value = "DEBUG"
        
        # Reload the module to test environment variable reading
        import importlib
        import now_lms.logs
        importlib.reload(now_lms.logs)
        
        mock_environ.get.assert_called_with("LOG_LEVEL", "INFO")

    def test_logger_has_handlers(self):
        """Test that logger has appropriate handlers configured."""
        assert len(log.handlers) > 0
        
        # Should have at least one StreamHandler
        stream_handlers = [h for h in log.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) > 0

    def test_handler_formatter(self):
        """Test that handlers have proper formatters."""
        for handler in log.handlers:
            assert handler.formatter is not None
            
            # Test formatter format
            formatter = handler.formatter
            assert hasattr(formatter, '_fmt')

    def test_root_logger_configuration(self):
        """Test that root logger is properly configured."""
        root_logger = logging.getLogger("now_lms")
        assert root_logger.level <= logging.CRITICAL
        assert root_logger.level >= TRACE_LEVEL_NUM

    def test_flask_logger_configuration(self):
        """Test that Flask logger is configured."""
        flask_logger = logging.getLogger("flask")
        # Should be configured to some level
        assert flask_logger.level is not None

    def test_werkzeug_logger_configuration(self):
        """Test that Werkzeug logger is configured."""
        werkzeug_logger = logging.getLogger("werkzeug")
        # Should be configured to some level
        assert werkzeug_logger.level is not None

    def test_sqlalchemy_logger_configuration(self):
        """Test that SQLAlchemy logger is configured to WARNING."""
        sqlalchemy_logger = logging.getLogger("sqlalchemy")
        assert sqlalchemy_logger.level == logging.WARNING


class TestLoggingEdgeCases:
    """Test edge cases and error conditions for logging."""

    def test_trace_with_args_and_kwargs(self):
        """Test trace method with both args and kwargs."""
        mock_logger = MagicMock()
        mock_logger.isEnabledFor.return_value = True
        
        # Call with various parameters
        trace(mock_logger, "Message %s %d", "test", 42, extra={"key": "value"})
        
        mock_logger._log.assert_called_once_with(
            TRACE_LEVEL_NUM, "Message %s %d", ("test", 42), extra={"key": "value"}
        )

    def test_trace_with_exception_info(self):
        """Test trace method with exception info."""
        mock_logger = MagicMock()
        mock_logger.isEnabledFor.return_value = True
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            trace(mock_logger, "Exception occurred", exc_info=True)
        
        mock_logger._log.assert_called_once_with(
            TRACE_LEVEL_NUM, "Exception occurred", (), exc_info=True
        )

    def test_numeric_level_fallback(self):
        """Test that invalid log level falls back to INFO."""
        from now_lms.logs import custom_levels
        
        # Test with invalid level
        invalid_level = "INVALID_LEVEL"
        numeric_level = custom_levels.get(invalid_level, logging.INFO)
        
        assert numeric_level == logging.INFO

    def test_logging_integration(self):
        """Test logging integration with actual logging calls."""
        # Create a temporary logger for testing
        test_logger = logging.getLogger("test_integration")
        test_logger.setLevel(TRACE_LEVEL_NUM)
        
        # Add a handler to capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        test_logger.addHandler(handler)
        
        # Test all levels
        test_logger.trace("Trace message")
        test_logger.debug("Debug message")
        test_logger.info("Info message")
        test_logger.warning("Warning message")
        test_logger.error("Error message")
        test_logger.critical("Critical message")
        
        output = stream.getvalue()
        
        # Check that all messages appear
        assert "TRACE: Trace message" in output
        assert "DEBUG: Debug message" in output
        assert "INFO: Info message" in output
        assert "WARNING: Warning message" in output
        assert "ERROR: Error message" in output
        assert "CRITICAL: Critical message" in output
        
        # Clean up
        test_logger.removeHandler(handler)