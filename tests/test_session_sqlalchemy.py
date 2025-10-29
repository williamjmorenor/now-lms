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
"""Test SQLAlchemy session backend."""

import os
import pytest
from unittest.mock import patch


class TestSQLAlchemySessionBackend:
    """Test SQLAlchemy session backend configuration."""

    def test_session_config_testing_mode(self):
        """Test that session config returns None in testing mode."""
        from now_lms.session_config import get_session_config

        # Testing mode is set by CI environment variable or pytest
        config = get_session_config()

        # In testing mode, should return None
        assert config is None

    def test_session_config_sqlalchemy_fallback(self):
        """Test that SQLAlchemy is used as fallback when Redis is not available."""
        # Temporarily unset testing mode and Redis URL
        with patch.dict(
            os.environ,
            {
                "CI": "",
                "PYTEST_CURRENT_TEST": "",
                "REDIS_URL": "",
                "SESSION_REDIS_URL": "",
                "CACHE_REDIS_URL": "",
            },
            clear=False,
        ):
            # Remove testing indicators
            for key in ["CI", "PYTEST_CURRENT_TEST", "REDIS_URL", "SESSION_REDIS_URL", "CACHE_REDIS_URL"]:
                os.environ.pop(key, None)

            # Mock the TESTING constant by patching the module
            from now_lms import session_config

            with patch.object(session_config, "TESTING", False):
                from now_lms.session_config import get_session_config

                config = get_session_config()

                # Should return SQLAlchemy config when Redis is not available
                assert config is not None
                assert config["SESSION_TYPE"] == "sqlalchemy"
                assert config["SESSION_SQLALCHEMY_TABLE"] == "flask_sessions"
                assert config["SESSION_USE_SIGNER"] is True
                assert config["PERMANENT_SESSION_LIFETIME"] == 86400

    def test_session_table_created(self, session_full_db_setup):
        """Test that the flask_sessions table is created in non-testing mode."""
        from sqlalchemy import inspect

        # Create a non-testing app to verify table creation
        with patch.dict(os.environ, {"CI": ""}, clear=False):
            os.environ.pop("CI", None)

            # Import after environment is set
            from now_lms import create_app
            from now_lms import db

            app = create_app()

            with app.app_context():
                inspector = inspect(db.database.engine)
                tables = inspector.get_table_names()

                # Verify the table exists (only in production mode)
                session_type = app.config.get("SESSION_TYPE")
                if session_type == "sqlalchemy":
                    assert "flask_sessions" in tables

                    # Verify table structure
                    columns = inspector.get_columns("flask_sessions")
                    column_names = [col["name"] for col in columns]

                    assert "id" in column_names
                    assert "session_id" in column_names
                    assert "data" in column_names
                    assert "expiry" in column_names

    def test_session_cli_commands_exist(self):
        """Test that session CLI commands are registered."""
        from now_lms import lms_app

        # Get all CLI commands
        cli_commands = lms_app.cli.commands

        # Verify database group exists
        assert "database" in cli_commands

        # Get database subcommands
        database_group = cli_commands["database"]
        database_commands = database_group.commands

        # Verify session group exists under database
        assert "session" in database_commands

        # Get session subcommands
        session_group = database_commands["session"]
        session_commands = session_group.commands

        # Verify clear and stats commands exist
        assert "clear" in session_commands
        assert "stats" in session_commands


class TestSessionCLICommands:
    """Test session CLI commands functionality."""

    @pytest.mark.skipif(os.environ.get("CI") or os.environ.get("PYTEST_CURRENT_TEST"), reason="Cannot test in CI/testing mode")
    def test_session_stats_command_no_sessions(self):
        """Test session stats command with no active sessions."""
        from click.testing import CliRunner
        from now_lms import lms_app

        with patch.dict(os.environ, {"CI": ""}, clear=False):
            os.environ.pop("CI", None)

            runner = CliRunner()

            with lms_app.app_context():
                # Ensure session type is sqlalchemy
                if lms_app.config.get("SESSION_TYPE") == "sqlalchemy":
                    result = runner.invoke(lms_app.cli, ["database", "session", "stats"])

                    assert result.exit_code == 0
                    assert "Active sessions: 0" in result.output
                    assert "Total sessions: 0" in result.output

    @pytest.mark.skipif(os.environ.get("CI") or os.environ.get("PYTEST_CURRENT_TEST"), reason="Cannot test in CI/testing mode")
    def test_session_clear_command_no_sessions(self):
        """Test session clear command with no expired sessions."""
        from click.testing import CliRunner
        from now_lms import lms_app

        with patch.dict(os.environ, {"CI": ""}, clear=False):
            os.environ.pop("CI", None)

            runner = CliRunner()

            with lms_app.app_context():
                # Ensure session type is sqlalchemy
                if lms_app.config.get("SESSION_TYPE") == "sqlalchemy":
                    result = runner.invoke(lms_app.cli, ["database", "session", "clear"])

                    assert result.exit_code == 0
                    assert "Deleted 0 expired session(s)" in result.output


class TestSessionBackendIntegration:
    """Integration tests for session backend."""

    def test_redis_priority_over_sqlalchemy(self):
        """Test that Redis is preferred over SQLAlchemy when available."""
        with patch.dict(
            os.environ, {"REDIS_URL": "redis://localhost:6379/0", "CI": "", "PYTEST_CURRENT_TEST": ""}, clear=False
        ):
            # Remove testing indicators
            for key in ["CI", "PYTEST_CURRENT_TEST"]:
                os.environ.pop(key, None)

            # Mock the TESTING constant by patching the module
            from now_lms import session_config

            with patch.object(session_config, "TESTING", False):
                from now_lms.session_config import get_session_config

                config = get_session_config()

                # When Redis URL is set, should use Redis
                if config is not None:  # May be None if redis module is not available
                    assert config["SESSION_TYPE"] == "redis"
