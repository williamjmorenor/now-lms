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
"""Test that configuration documentation matches the code implementation."""

import re
from pathlib import Path


def test_config_documentation_variable_names():
    """Verify that documented configuration variable names match actual code usage."""
    # Read documentation
    doc_path = Path(__file__).parent.parent / "docs" / "setup-conf.md"
    doc_content = doc_path.read_text()

    # Variables that should be documented as NOW_LMS_DATA_DIR, not CUSTOM_DATA_DIR
    assert "NOW_LMS_DATA_DIR" in doc_content, "NOW_LMS_DATA_DIR should be documented"
    assert "CUSTOM_DATA_DIR" not in doc_content, "CUSTOM_DATA_DIR is incorrect (should be NOW_LMS_DATA_DIR)"

    # Variables that should be documented as NOW_LMS_THEMES_DIR, not CUSTOM_THEMES_DIR
    assert "NOW_LMS_THEMES_DIR" in doc_content, "NOW_LMS_THEMES_DIR should be documented"
    assert "CUSTOM_THEMES_DIR" not in doc_content, "CUSTOM_THEMES_DIR is incorrect (should be NOW_LMS_THEMES_DIR)"


def test_session_redis_url_documented():
    """Verify that SESSION_REDIS_URL is documented."""
    doc_path = Path(__file__).parent.parent / "docs" / "setup-conf.md"
    doc_content = doc_path.read_text()

    assert "SESSION_REDIS_URL" in doc_content, "SESSION_REDIS_URL should be documented"


def test_config_file_example_does_not_include_directory_paths():
    """Verify that config file examples don't incorrectly show directory paths.
    
    Directory paths like NOW_LMS_DATA_DIR and NOW_LMS_THEMES_DIR must be
    environment variables because they're read during early module initialization,
    before config files are loaded.
    """
    doc_path = Path(__file__).parent.parent / "docs" / "setup-conf.md"
    doc_content = doc_path.read_text()

    # Find the config file format example section
    config_example_pattern = r"```ini\n(.*?)```"
    matches = re.findall(config_example_pattern, doc_content, re.DOTALL)

    for match in matches:
        # Check if this is a config file example (not a systemd or docker example)
        if "SECRET_KEY" in match and "DATABASE_URL" in match:
            # Check each line that's not a comment
            for line in match.split("\n"):
                line = line.strip()
                # Skip comments and empty lines
                if line.startswith("#") or not line:
                    continue
                # Directory paths should not be in actual config file examples
                assert "NOW_LMS_DATA_DIR" not in line, (
                    f"NOW_LMS_DATA_DIR should not be in config file examples "
                    f"(it must be an environment variable). Found in: {line}"
                )
                assert "NOW_LMS_THEMES_DIR" not in line, (
                    f"NOW_LMS_THEMES_DIR should not be in config file examples "
                    f"(it must be an environment variable). Found in: {line}"
                )


def test_critical_environment_variables_are_documented():
    """Verify that all critical environment variables used in code are documented."""
    doc_path = Path(__file__).parent.parent / "docs" / "setup-conf.md"
    doc_content = doc_path.read_text()

    critical_vars = [
        "SECRET_KEY",
        "DATABASE_URL",
        "NOW_LMS_DATA_DIR",
        "NOW_LMS_THEMES_DIR",
        "NOW_LMS_LANG",
        "NOW_LMS_CURRENCY",
        "NOW_LMS_TIMEZONE",
        "REDIS_URL",
        "CACHE_REDIS_URL",
        "SESSION_REDIS_URL",
        "MAIL_SERVER",
        "MAIL_PORT",
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
        "LOG_LEVEL",
        "NOW_LMS_WORKERS",
        "NOW_LMS_THREADS",
        "NOW_LMS_AUTO_MIGRATE",
        "NOW_LMS_FORCE_HTTPS",
        "NOW_LMS_DEMO_MODE",
    ]

    for var in critical_vars:
        assert var in doc_content, f"Critical variable {var} should be documented"
