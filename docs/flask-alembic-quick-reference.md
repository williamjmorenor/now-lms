# Guía Rápida: flask-alembic

## Instalación

```bash
pip install flask-alembic==3.2.0 alembic==1.18.1
```

## Configuración Básica

```python
# app/__init__.py
from flask import Flask
from flask_alembic import Alembic

alembic = Alembic()

def create_app():
    app = Flask(__name__)
    
    # Configurar ruta de migraciones
    from os.path import abspath, dirname, join
    migrations_dir = abspath(join(dirname(__file__), "migrations"))
    app.config["ALEMBIC"] = {"script_location": migrations_dir}
    
    # Inicializar
    from app.db import database
    database.init_app(app)
    alembic.init_app(app)
    
    return app
```

## Comandos Principales

```bash
# Inicializar base de datos
lmsctl database init

# Migrar a la última versión
lmsctl database migrate
# O: flask alembic upgrade

# Ver versión actual
flask alembic current

# Ver historial
flask alembic history

# Retroceder una migración
flask alembic downgrade -1

# Retroceder a base
flask alembic downgrade base
```

## Crear Nueva Migración

### Método 1: Manual (Recomendado para NOW LMS)

1. Crear archivo: `app/migrations/20260125_120000_descripcion.py`
2. Copiar estructura de migración existente
3. Implementar `upgrade()` y `downgrade()`

### Método 2: Auto-generación

```bash
flask alembic revision -m "descripcion del cambio"
```

## Estructura de Migración

```python
"""Descripción del cambio

Revision ID: 20260125_120000
Revises: 20260120_100000
Create Date: 2026-01-25 12:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260125_120000"
down_revision = "20260120_100000"  # None si es la primera
branch_labels = None
depends_on = None


def upgrade():
    """Cambios hacia adelante."""
    # Verificar si el cambio ya existe (idempotencia)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if "tabla" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("tabla")]
        
        if "nueva_columna" not in columns:
            op.add_column(
                "tabla",
                sa.Column("nueva_columna", sa.String(255), nullable=False, server_default="valor")
            )


def downgrade():
    """Revertir cambios."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if "tabla" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("tabla")]
        
        if "nueva_columna" in columns:
            op.drop_column("tabla", "nueva_columna")
```

## Mejores Prácticas

1. ✅ **Migraciones Idempotentes**: Verificar si el cambio ya existe
2. ✅ **Valores por Defecto**: Usar `server_default` para columnas NOT NULL
3. ✅ **Documentación Clara**: Explicar el propósito del cambio
4. ✅ **Testing**: Probar upgrade → downgrade → upgrade
5. ✅ **Multi-DB**: Probar en SQLite, PostgreSQL y MySQL

## Configuración de Auto-Migración

```bash
# Variable de entorno
export APP_AUTO_MIGRATE=1
```

```python
# app/config/__init__.py
AUTO_MIGRATE = environ.get("APP_AUTO_MIGRATE", "0").strip().lower() in {"1", "true", "yes"}

# app/__init__.py
if AUTO_MIGRATE:
    with app.app_context():
        alembic.upgrade()
```

## Operaciones Comunes

### Agregar Columna

```python
op.add_column(
    "tabla",
    sa.Column("columna", sa.String(255), nullable=False, server_default="valor")
)
```

### Eliminar Columna

```python
op.drop_column("tabla", "columna")
```

### Crear Tabla

```python
op.create_table(
    "nueva_tabla",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("nombre", sa.String(255), nullable=False),
    sa.Column("activo", sa.Boolean, server_default=sa.true())
)
```

### Eliminar Tabla

```python
op.drop_table("tabla")
```

### Crear Índice

```python
op.create_index("ix_tabla_columna", "tabla", ["columna"])
```

### Eliminar Índice

```python
op.drop_index("ix_tabla_columna", table_name="tabla")
```

### Migración de Datos

```python
# Primero: cambio de esquema
op.add_column("users", sa.Column("full_name", sa.String(255)))

# Segundo: migración de datos
conn = op.get_bind()
conn.execute(
    sa.text("""
        UPDATE users 
        SET full_name = first_name || ' ' || last_name
        WHERE full_name IS NULL
    """)
)
```

## Testing

```python
# tests/test_alembic_upgrade.py
def test_alembic_upgrade_app_context(monkeypatch):
    """Test completo de migraciones."""
    # 1. Crear app de test
    app = create_app(app_name="test_app", testing=True)
    
    with app.app_context():
        # 2. Destruir todo
        db.drop_all()
        
        # 3. Crear esquema base
        initial_setup(flask_app=app)
        
        # 4. Marcar como actualizado
        alembic.stamp("head")
        
        # 5. Test upgrade (no debe hacer nada)
        alembic.upgrade()
        
        # 6. Test downgrade
        alembic.downgrade("base")
        
        # 7. Test upgrade de nuevo
        alembic.upgrade()
        
        # 8. Verificar versión final
        version = db.session.execute(
            db.text("SELECT version_num FROM alembic_version")
        ).scalar()
        assert version is not None
```

## Solución de Problemas

### Error: "Can't locate revision identified by 'XXX'"

```bash
# Verificar versión actual
flask alembic current

# Ver historial disponible
flask alembic history

# Si la BD está corrupta, marcar manualmente
flask alembic stamp head
```

### Error: "Column already exists"

**Solución**: Hacer migraciones idempotentes verificando existencia antes de crear.

### Error: "Target database is not up to date"

```bash
# Actualizar a la última versión
flask alembic upgrade
```

## Variables de Entorno

```bash
# Base de datos
DATABASE_URL=postgresql+pg8000://user:pass@localhost/dbname

# Auto-migración
APP_AUTO_MIGRATE=1

# Modo de desarrollo (opcional)
FLASK_ENV=development
```

## Recursos

- [Documentación Completa (Español)](flask-alembic-implementation.md)
- [Full Documentation (English)](flask-alembic-implementation-en.md)
- [Alembic Official Docs](https://alembic.sqlalchemy.org/)
- [flask-alembic GitHub](https://github.com/davidism/flask-alembic)

---

*Guía Rápida - NOW LMS flask-alembic Implementation*
