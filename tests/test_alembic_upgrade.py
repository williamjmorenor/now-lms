import os
from sqlalchemy.pool import StaticPool


def test_alembic_upgrade_app_context(monkeypatch):
    """
    Crea una app independiente y ejecuta alembic.upgrade() dentro de su contexto.
    Respeta DATABASE_URL si está definida; si no, usa SQLite en memoria.
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

    # Ejecutar migraciones dentro del contexto de la app
    with app.app_context():
        # Inicializar esquema base si la BD está vacía
        initial_setup(with_examples=False, flask_app=app)
        # Ejecutar migraciones
        alembic.upgrade()

        # Validar que existe una versión en alembic_version
        from now_lms.db import database as db

        conn = db.session.connection()
        version = conn.execute(db.text("SELECT version_num FROM alembic_version")).scalar()
        assert version is not None, "La tabla alembic_version debe contener la versión actual"

        # Cerrar sesión de forma explícita para evitar problemas de rollback en SQLite in-memory
        db.session.close()
