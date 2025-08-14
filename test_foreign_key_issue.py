#!/usr/bin/env python3
"""
Test to reproduce the foreign key constraint issue described in the GitHub issue.
"""

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

from tests.conftest import create_app
from now_lms.db import database, Usuario, Curso
from now_lms.auth import proteger_passwd


@event.listens_for(Engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    """Enable foreign key constraints for SQLite."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def test_foreign_key_constraint_issue():
    """Test that reproduces the foreign key constraint issue when foreign keys are enabled."""
    
    # Create app with foreign key enforcement enabled
    app = create_app(testing=True, database_uri="sqlite:///:memory:")
    
    with app.app_context():
        # Create tables
        database.create_all()
        
        # First, let's try to create a course without creating the user first
        # This should fail if foreign key constraints were enabled
        
        curso = Curso(
            codigo="test_course",
            nombre="Test Course",
            descripcion_corta="Test course description",
            descripcion="Test course description",
            estado="draft",
            pagado=False,
            creado_por="instructor1",  # This user doesn't exist
        )
        
        database.session.add(curso)
        
        # This should raise an IntegrityError due to foreign key constraint
        with pytest.raises(Exception) as exc_info:
            database.session.commit()
        
        print(f"Exception: {exc_info.value}")
        
        # Rollback the failed transaction
        database.session.rollback()
        
        # Now create the user first
        instructor = Usuario(
            usuario="instructor1",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)
        database.session.commit()
        
        # Now try to create the course again - this should work
        curso2 = Curso(
            codigo="test_course2",
            nombre="Test Course 2",
            descripcion_corta="Test course description",
            descripcion="Test course description",
            estado="draft",
            pagado=False,
            creado_por="instructor1",  # This user now exists
        )
        
        database.session.add(curso2)
        database.session.commit()  # This should succeed
        
        print("Test completed successfully - course created after user was created")


if __name__ == "__main__":
    test_foreign_key_constraint_issue()