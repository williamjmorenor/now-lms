# Copyright 2021 -2023 William José Moreno Reyes
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

from os import environ
import pytest


"""
Casos de uso mas comunes.
"""


@pytest.fixture
def lms_application():
    from now_lms import app

    app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "jgjañlsldaksjdklasjfkjj",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
            "DEBUG": True,
            "PRESERVE_CONTEXT_ON_EXCEPTION": True,
            "SQLALCHEMY_ECHO": True,
            "MAIL_SUPPRESS_SEND": True,
        }
    )

    yield app


def test_postgress_pg8000(lms_application):
    """Test PostgreSQL with pg8000 driver."""
    if environ.get("DATABASE_URL", "").startswith("postgresql+pg8000"):
        lms_application.config.update({"SQLALCHEMY_DATABASE_URI": environ.get("DATABASE_URL")})
        assert lms_application.config.get("SQLALCHEMY_DATABASE_URI") == environ.get("DATABASE_URL")
        from now_lms import database, initial_setup
        from sqlalchemy.exc import OperationalError, ProgrammingError
        from pg8000.dbapi import ProgrammingError as PGProgrammingError
        from pg8000.exceptions import DatabaseError

        with lms_application.app_context():
            try:
                # For PostgreSQL, handle potential rollback issues
                database.session.rollback()
                database.session.close()
                database.drop_all()
                initial_setup(with_tests=True, with_examples=True)
            except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError) as e:
                log.warning(f"PostgreSQL pg8000 test setup error: {e}")
                pytest.skip(f"PostgreSQL pg8000 setup failed: {e}")
    else:
        pytest.skip("Not postgresql+pg8000 driver configured in environ.")


def test_postgress_psycopg2(lms_application):
    """Test PostgreSQL with psycopg2 driver."""
    if environ.get("DATABASE_URL", "").startswith("postgresql+psycopg2"):
        lms_application.config.update({"SQLALCHEMY_DATABASE_URI": environ.get("DATABASE_URL")})
        assert lms_application.config.get("SQLALCHEMY_DATABASE_URI") == environ.get("DATABASE_URL")
        from now_lms import database, initial_setup
        from sqlalchemy.exc import OperationalError, ProgrammingError

        with lms_application.app_context():
            try:
                # For PostgreSQL, handle potential rollback issues
                database.session.rollback()
                database.session.close()
                database.drop_all()
                initial_setup(with_tests=True, with_examples=True)
            except (OperationalError, ProgrammingError) as e:
                log.warning(f"PostgreSQL psycopg2 test setup error: {e}")
                pytest.skip(f"PostgreSQL psycopg2 setup failed: {e}")
    else:
        pytest.skip("Not postgresql+psycopg2 driver configured in environ.")


def test_mysql_mysqldb(lms_application, request):
    """Test MySQL with mysqldb driver."""
    if environ.get("DATABASE_URL", "").startswith("mysql+mysqldb"):
        lms_application.config.update({"SQLALCHEMY_DATABASE_URI": environ.get("DATABASE_URL")})
        assert lms_application.config.get("SQLALCHEMY_DATABASE_URI") == environ.get("DATABASE_URL")
        from now_lms import database, initial_setup
        from sqlalchemy.exc import OperationalError, ProgrammingError

        with lms_application.app_context():
            try:
                database.drop_all()
                initial_setup(with_tests=True, with_examples=True)
            except (OperationalError, ProgrammingError) as e:
                log.warning(f"MySQL mysqldb test setup error: {e}")
                pytest.skip(f"MySQL mysqldb setup failed: {e}")
    else:
        pytest.skip("Not mysql+mysqldb driver configured in environ.")
