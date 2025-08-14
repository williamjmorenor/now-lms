#!/usr/bin/env python3
"""
Test to reproduce the foreign key constraint issue by adding foreign key constraints
to the audit fields and then testing the scenario.
"""

import pytest
from sqlalchemy import event, Column, String, ForeignKey
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
import sqlite3

from tests.conftest import create_app
from now_lms.db import database, Usuario, Curso, BaseTabla, LLAVE_FORANEA_USUARIO
from now_lms.auth import proteger_passwd


@event.listens_for(Engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    """Enable foreign key constraints for SQLite."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def test_foreign_key_constraint_with_fk_enabled():
    """Test that reproduces the foreign key constraint issue by temporarily adding FK constraints."""
    
    # Temporarily modify BaseTabla to have foreign key constraints
    original_creado_por = BaseTabla.creado_por
    original_modificado_por = BaseTabla.modificado_por
    
    # Add foreign key constraints to audit fields
    BaseTabla.creado_por = Column(String(150), ForeignKey(LLAVE_FORANEA_USUARIO), nullable=True)
    BaseTabla.modificado_por = Column(String(150), ForeignKey(LLAVE_FORANEA_USUARIO), nullable=True)
    
    app = create_app(testing=True, database_uri="sqlite:///:memory:")
    
    try:
        with app.app_context():
            # Create tables with the new foreign key constraints
            database.create_all()
            
            # Try to create a course without creating the user first
            # This should fail due to foreign key constraint
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
            try:
                database.session.commit()
                print("ERROR: Expected foreign key constraint failure but commit succeeded")
                return False
            except IntegrityError as e:
                print(f"SUCCESS: Got expected foreign key constraint error: {e}")
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
            
            print("SUCCESS: Course created successfully after user was created")
            return True
    
    finally:
        # Restore original audit fields
        BaseTabla.creado_por = original_creado_por
        BaseTabla.modificado_por = original_modificado_por


if __name__ == "__main__":
    test_foreign_key_constraint_with_fk_enabled()