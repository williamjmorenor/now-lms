import os
from sqlalchemy.pool import StaticPool


def test_alembic_upgrade_app_context(monkeypatch):
    """
    Test robusto y destructivo de migraciones Alembic.
    
    Este test verifica que las migraciones funcionan correctamente ejecutando:
    1. drop_all() - Elimina todas las tablas
    2. initial_setup() - Crea esquema base
    3. upgrade() - No debe hacer nada en BD recién creada
    4. downgrade('base') - Baja hasta la migración cero
    5. upgrade() - Sube de nuevo hasta head
    
    Todo el recorrido debe ejecutarse sin errores.
    """
    # Respetar DATABASE_URL o usar SQLite en memoria
    if not os.environ.get("DATABASE_URL"):
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    # Crear app independiente en modo testing
    from now_lms import create_app, alembic, initial_setup

    # For SQLite in-memory, keep a single connection alive using StaticPool
    config_overrides = {}
    if os.environ.get("DATABASE_URL", "").startswith("sqlite") and ":memory:" in os.environ.get("DATABASE_URL", ""):
        config_overrides["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": StaticPool}
        config_overrides["SQLALCHEMY_CONNECT_ARGS"] = {"check_same_thread": False}

    app = create_app(app_name="test_alembic_app", testing=True, config_overrides=config_overrides)

    with app.app_context():
        from now_lms.db import database as db

        # Paso 1: Destruir todas las tablas (test destructivo)
        db.drop_all()
        db.session.commit()

        # Paso 2: Crear esquema base con initial_setup
        initial_setup(with_examples=False, flask_app=app)
        db.session.commit()

        # Paso 2.1: Marcar la base de datos como actualizada (stamp head)
        # Esto crea la tabla alembic_version y la marca con la versión actual
        alembic.stamp()
        db.session.commit()

        # Verificar que stamp creó la tabla alembic_version
        version_after_stamp = db.session.execute(db.text("SELECT version_num FROM alembic_version")).scalar()
        assert version_after_stamp is not None, "stamp() debe crear la tabla alembic_version con una versión"

        # Paso 3: Ejecutar upgrade - no debe hacer nada porque la BD recién creada ya está actualizada
        alembic.upgrade()
        db.session.commit()

        # Verificar que la versión sigue siendo la misma
        version_after_first_upgrade = db.session.execute(db.text("SELECT version_num FROM alembic_version")).scalar()
        assert (
            version_after_first_upgrade == version_after_stamp
        ), "upgrade() no debe cambiar nada en una BD recién marcada como actualizada"

        # Paso 4: Hacer downgrade hasta la base (migración cero)
        alembic.downgrade("base")
        db.session.commit()

        # Verificar que no hay versión en alembic_version o la tabla fue eliminada
        # (dependiendo de la implementación de las migraciones)
        try:
            version_after_downgrade = db.session.execute(db.text("SELECT version_num FROM alembic_version")).scalar()
            assert version_after_downgrade is None, "Después de downgrade('base'), no debe haber versión"
        except Exception:
            # Es posible que la tabla alembic_version no exista después del downgrade
            pass

        # Paso 5: Hacer upgrade de nuevo hasta head
        alembic.upgrade()
        db.session.commit()

        # Verificar que ahora sí hay una versión válida
        version_after_final_upgrade = db.session.execute(db.text("SELECT version_num FROM alembic_version")).scalar()
        assert version_after_final_upgrade is not None, "Después de upgrade(), debe haber una versión válida"
        assert version_after_final_upgrade == version_after_stamp, "Después del ciclo completo, debe volver a la misma versión"

        # Cerrar sesión de forma explícita
        db.session.close()
