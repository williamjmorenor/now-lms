#!/usr/bin/env python3
"""
Test to reproduce the foreign key constraint issue with FK constraints enabled.
"""

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
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


def test_reproduce_fk_issue():
    """Test that reproduces the foreign key constraint issue."""
    
    app = create_app(testing=True, database_uri="sqlite:///:memory:")
    
    with app.app_context():
        # Create tables
        database.create_all()
        
        print("Testing foreign key constraint enforcement...")
        
        # Try to create a course with a non-existent user in creado_por
        curso = Curso(
            codigo="test_course",
            nombre="Test Course",
            descripcion_corta="Test course description",
            descripcion="Test course description",
            estado="draft",
            pagado=False,
            creado_por="nonexistent_user",  # This user doesn't exist
        )
        
        database.session.add(curso)
        
        try:
            database.session.commit()
            print("ISSUE: Course was created even though user doesn't exist!")
            
            # Check if course was actually created
            created_course = database.session.execute(
                database.select(Curso).filter_by(codigo="test_course")
            ).scalar_one_or_none()
            
            if created_course:
                print(f"Course found: {created_course.nombre}, creado_por: {created_course.creado_por}")
            
            return False
            
        except IntegrityError as e:
            print(f"EXPECTED: Foreign key constraint error: {e}")
            database.session.rollback()
            
            # Now create the user first
            print("Creating user first...")
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
            print("User created successfully")
            
            # Now try to create the course with valid user
            curso2 = Curso(
                codigo="test_course2",
                nombre="Test Course 2",
                descripcion_corta="Test course description",
                descripcion="Test course description",
                estado="draft",
                pagado=False,
                creado_por="instructor1",  # This user exists
            )
            
            database.session.add(curso2)
            database.session.commit()
            print("Course created successfully with valid user")
            
            return True


if __name__ == "__main__":
    test_reproduce_fk_issue()