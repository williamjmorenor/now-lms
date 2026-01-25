# Resumen de Implementación de flask-alembic en NOW LMS

Este documento proporciona un resumen completo de cómo se implementó `flask-alembic` en el proyecto NOW LMS, incluyendo todos los puntos clave necesarios para replicar esta implementación en otro proyecto Flask.

## Tabla de Contenidos

1. [Descripción General](#descripcion-general)
2. [Dependencias y Requisitos](#dependencias-y-requisitos)
3. [Estructura de Archivos](#estructura-de-archivos)
4. [Configuración de la Aplicación](#configuracion-de-la-aplicacion)
5. [Estructura de las Migraciones](#estructura-de-las-migraciones)
6. [Comandos CLI](#comandos-cli)
7. [Automatización de Migraciones](#automatizacion-de-migraciones)
8. [Testing](#testing)
9. [Mejores Prácticas](#mejores-practicas)
10. [Guía Paso a Paso para Replicar](#guia-paso-a-paso-para-replicar)

---

## Descripción General

`flask-alembic` es una extensión de Flask que integra Alembic, una herramienta de migración de bases de datos para SQLAlchemy. En NOW LMS, se utiliza para gestionar cambios en el esquema de la base de datos de forma programática y versionada.

**Beneficios principales:**
- Control de versiones del esquema de base de datos
- Migraciones hacia adelante y hacia atrás (upgrade/downgrade)
- Soporte para múltiples bases de datos (SQLite, PostgreSQL, MySQL)
- Integración perfecta con Flask y SQLAlchemy
- Automatización de migraciones en producción

---

## Dependencias y Requisitos

### Paquetes Python Requeridos

```txt
# requirements.txt
alembic==1.18.1
flask-alembic==3.2.0
```

Estos se instalan junto con las dependencias principales del proyecto.

### Versiones de Python

- Python >= 3.11 (NOW LMS)
- Compatible con Python 3.8+

---

## Estructura de Archivos

```
proyecto/
├── app_package/
│   ├── __init__.py              # Inicialización de Flask app y extensiones
│   ├── migrations/              # Directorio de migraciones
│   │   ├── script.py.mako      # Plantilla para nuevas migraciones
│   │   ├── 20260105_145517_add_feature.py
│   │   ├── 20260109_152634_add_tables.py
│   │   └── ...
│   ├── cli.py                   # Comandos CLI personalizados
│   └── config/
│       └── __init__.py          # Configuración de la aplicación
├── tests/
│   └── test_alembic_upgrade.py  # Tests de migraciones
├── requirements.txt
└── development.txt
```

### Ubicación del Directorio de Migraciones

**Punto clave:** En NOW LMS, las migraciones se almacenan **dentro del paquete de la aplicación** (`now_lms/migrations/`), no en la raíz del proyecto. Esto permite:
- Distribuir las migraciones con el paquete PyPI
- Mantener las migraciones versionadas con el código
- Facilitar el despliegue en diferentes entornos

---

## Configuración de la Aplicación

### 1. Inicialización en `__init__.py`

```python
# app_package/__init__.py

from flask import Flask
from flask_alembic import Alembic
from flask_sqlalchemy import SQLAlchemy

# Crear la instancia global de Alembic
alembic: Alembic = Alembic()
database = SQLAlchemy()

def inicializa_extenciones_terceros(flask_app: Flask) -> None:
    """Inicia extensiones de terceros."""
    with flask_app.app_context():
        from os.path import abspath, dirname, join

        # IMPORTANTE: Configurar la ruta absoluta al directorio de migraciones
        migrations_dir = abspath(join(dirname(__file__), "migrations"))
        flask_app.config.from_mapping({
            "ALEMBIC": {
                "script_location": migrations_dir
            }
        })

        # Inicializar extensiones en orden
        database.init_app(flask_app)
        alembic.init_app(flask_app)

def create_app(app_name="myapp", testing=False, config_overrides=None):
    """Factory function para crear la aplicación Flask."""
    flask_app = Flask(app_name)
    
    # Aplicar configuración base
    flask_app.config.from_mapping(BASE_CONFIG)
    
    # Aplicar overrides si se proporcionan
    if config_overrides:
        flask_app.config.update(config_overrides)
    
    # Inicializar extensiones dentro del contexto de la app
    with flask_app.app_context():
        inicializa_extenciones_terceros(flask_app)
        # ... registrar blueprints, etc.
    
    return flask_app

# Crear la aplicación principal
app = create_app()
```

### 2. Configuración de Variables de Entorno

```python
# app_package/config/__init__.py

from os import environ

# Variable para habilitar auto-migraciones en producción
VALORES_TRUE = {"1", "true", "yes", "on", "development", "dev"}
AUTO_MIGRATE = environ.get("APP_AUTO_MIGRATE", "0").strip().lower() in VALORES_TRUE
```

### 3. Lógica de Auto-Migración

```python
# app_package/__init__.py

def init_app(with_examples=False, flask_app=None):
    """Función auxiliar para iniciar la aplicación."""
    from app_package.db.tools import check_db_access, database_is_populated
    
    app_to_use = flask_app if flask_app is not None else app
    
    DB_ACCESS = check_db_access(app_to_use)
    DB_INICIALIZADA = database_is_populated(app_to_use)
    
    if DB_ACCESS:
        if DB_INICIALIZADA:
            # Si AUTO_MIGRATE está habilitado, ejecutar migraciones automáticamente
            if AUTO_MIGRATE:
                try:
                    with app_to_use.app_context():
                        alembic.upgrade()
                    log.info("Database migrated successfully.")
                except Exception as e:
                    log.error(f"Error during database migration: {e}")
                    return False
            return True
        else:
            # Primera vez: crear esquema base
            initial_setup(with_examples=with_examples, flask_app=app_to_use)
            return True
    
    log.warning("Could not access the database.")
    return False
```

---

## Estructura de las Migraciones

### Plantilla de Migración (script.py.mako)

```mako
# app_package/migrations/script.py.mako

"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
```

### Ejemplo de Migración Completa

```python
# app_package/migrations/20260105_145517_add_allow_unverified_email_login.py

"""Add allow_unverified_email_login to Configuracion

Revision ID: 20260105_145517
Revises:
Create Date: 2026-01-05 14:55:17

This migration adds the 'allow_unverified_email_login' field to the
Configuracion table to allow administrators to enable restricted access
for users who have not verified their email addresses.

The default value is False to maintain backward compatibility.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260105_145517"
down_revision = None  # Primera migración
branch_labels = None
depends_on = None


def upgrade():
    """Add allow_unverified_email_login column to configuracion table."""
    # Verificar si la columna ya existe antes de agregarla
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if "configuracion" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("configuracion")]
        
        if "allow_unverified_email_login" not in columns:
            # Agregar columna con valor por defecto False para compatibilidad
            op.add_column(
                "configuracion",
                sa.Column(
                    "allow_unverified_email_login",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false()
                ),
            )


def downgrade():
    """Remove allow_unverified_email_login column from configuracion table."""
    # Verificar si la columna existe antes de eliminarla
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if "configuracion" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("configuracion")]
        
        if "allow_unverified_email_login" in columns:
            op.drop_column("configuracion", "allow_unverified_email_login")
```

### Convención de Nombres

NOW LMS utiliza el formato: `YYYYMMDD_HHMMSS_descripcion.py`

**Ejemplos:**
- `20260105_145517_add_allow_unverified_email_login.py`
- `20260109_152634_add_missing_tables.py`
- `20260110_035505_add_blog_cover_image.py`

**Ventajas:**
- Orden cronológico automático
- Fácil identificación de cuándo se creó
- Descripción clara del propósito

---

## Comandos CLI

### Integración con Flask CLI

```python
# app_package/cli.py

import click
from flask.cli import FlaskGroup
from app_package import alembic, app, initial_setup

@click.group(
    cls=FlaskGroup,
    create_app=lambda: app,
    help="CLI para administración de la aplicación."
)
def command() -> None:
    """Línea de comandos para administración de la aplicación."""
    pass

@app.cli.group()
def database():
    """Database administration tools."""
    pass

@database.command()
@click.option("--with-examples", is_flag=True, default=False)
def init(with_examples=False):
    """Initialize a new database."""
    with app.app_context():
        from app_package.db.tools import database_is_populated
        
        if not database_is_populated(app):
            initial_setup(with_examples)
        else:
            click.echo("Database already initialized.")

@database.command()
def migrate():
    """Update database schema to latest version."""
    with app.app_context():
        alembic.upgrade()
        click.echo("Database migrated successfully.")

# Comandos adicionales de alembic disponibles a través de flask-alembic:
# flask alembic upgrade    - Migrar a la última versión
# flask alembic downgrade  - Retroceder migraciones
# flask alembic current    - Mostrar versión actual
# flask alembic history    - Mostrar historial de migraciones
# flask alembic show       - Mostrar detalles de una migración
```

### Uso de Comandos

```bash
# Inicializar base de datos nueva
lmsctl database init

# Migrar base de datos existente
lmsctl database migrate

# O usando Flask CLI directamente
flask database migrate

# Comandos de flask-alembic
flask alembic upgrade       # Actualizar a la última versión
flask alembic downgrade -1  # Retroceder una migración
flask alembic current       # Ver versión actual
flask alembic history       # Ver historial de migraciones
```

---

## Automatización de Migraciones

### Configuración de Auto-Migración

```bash
# Variable de entorno para habilitar auto-migraciones
export APP_AUTO_MIGRATE=1
```

### Flujo de Auto-Migración

1. La aplicación verifica si la base de datos está poblada
2. Si está poblada y `AUTO_MIGRATE=1`, ejecuta `alembic.upgrade()`
3. Si no está poblada, ejecuta `initial_setup()` y marca como `head`
4. Logs apropiados para cada caso

**Uso recomendado:**
- ✅ Desarrollo: `AUTO_MIGRATE=1` para sincronizar cambios automáticamente
- ✅ Staging: `AUTO_MIGRATE=1` para probar migraciones
- ⚠️ Producción: Preferible ejecutar migraciones manualmente antes del despliegue

---

## Testing

### Test de Migraciones Robusto

```python
# tests/test_alembic_upgrade.py

import os
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.pool import StaticPool


def test_alembic_upgrade_app_context(monkeypatch):
    """
    Test robusto y destructivo de migraciones Alembic.
    
    Este test verifica que las migraciones funcionan correctamente ejecutando:
    1. drop_all() - Elimina todas las tablas
    2. initial_setup() - Crea esquema base
    3. stamp('head') - Marca BD como actualizada
    4. upgrade() - No debe hacer nada en BD recién creada
    5. downgrade('base') - Baja hasta la migración cero
    6. upgrade() - Sube de nuevo hasta head
    
    Todo el recorrido debe ejecutarse sin errores.
    """
    # Respetar DATABASE_URL o usar SQLite en memoria
    if not os.environ.get("DATABASE_URL"):
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    
    # Crear app independiente en modo testing
    from app_package import create_app, alembic, initial_setup
    
    # Para SQLite en memoria, mantener conexión viva con StaticPool
    config_overrides = {}
    if os.environ.get("DATABASE_URL", "").startswith("sqlite") and \
       ":memory:" in os.environ.get("DATABASE_URL", ""):
        config_overrides["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": StaticPool}
        config_overrides["SQLALCHEMY_CONNECT_ARGS"] = {"check_same_thread": False}
    
    app = create_app(
        app_name="test_alembic_app",
        testing=True,
        config_overrides=config_overrides
    )
    
    with app.app_context():
        from app_package.db import database as db
        
        # Paso 1: Destruir todas las tablas (test destructivo)
        db.drop_all()
        db.session.commit()
        
        # Paso 2: Crear esquema base con initial_setup
        initial_setup(with_examples=False, flask_app=app)
        db.session.commit()
        
        # Paso 2.1: Marcar la base de datos como actualizada (stamp head)
        alembic.stamp("head")
        db.session.commit()
        
        # Verificar que stamp creó la tabla alembic_version
        version_after_stamp = db.session.execute(
            db.text("SELECT version_num FROM alembic_version")
        ).scalar()
        assert version_after_stamp is not None
        
        # Paso 3: Ejecutar upgrade - no debe hacer nada
        alembic.upgrade()
        db.session.commit()
        
        # Verificar que la versión sigue siendo la misma
        version_after_first_upgrade = db.session.execute(
            db.text("SELECT version_num FROM alembic_version")
        ).scalar()
        assert version_after_first_upgrade == version_after_stamp
        
        # Paso 4: Hacer downgrade hasta la base (migración cero)
        alembic.downgrade("base")
        db.session.commit()
        
        # Verificar que no hay versión en alembic_version
        try:
            version_after_downgrade = db.session.execute(
                db.text("SELECT version_num FROM alembic_version")
            ).scalar()
            assert version_after_downgrade is None
        except (OperationalError, ProgrammingError):
            # La tabla alembic_version no existe, lo cual es válido
            pass
        
        # Paso 5: Hacer upgrade de nuevo hasta head
        alembic.upgrade()
        db.session.commit()
        
        # Verificar que ahora sí hay una versión válida
        version_after_final_upgrade = db.session.execute(
            db.text("SELECT version_num FROM alembic_version")
        ).scalar()
        assert version_after_final_upgrade is not None
        
        # Cerrar sesión de forma explícita
        db.session.close()
```

### Ejecución de Tests

```bash
# Test específico de migraciones
pytest tests/test_alembic_upgrade.py -v

# Test completo de la suite
pytest --tb=short -q --cov=app_package
```

---

## Mejores Prácticas

### 1. Migraciones Idempotentes

**Siempre verificar si el cambio ya existe:**

```python
def upgrade():
    """Add column if it doesn't exist."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if "table_name" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("table_name")]
        
        if "new_column" not in columns:
            op.add_column("table_name", sa.Column("new_column", sa.String(255)))
```

**Beneficios:**
- Evita errores al re-ejecutar migraciones
- Permite recuperarse de fallos parciales
- Facilita el testing y desarrollo

### 2. Valores por Defecto

**Siempre establecer valores por defecto apropiados:**

```python
op.add_column(
    "users",
    sa.Column(
        "is_active",
        sa.Boolean(),
        nullable=False,
        server_default=sa.true()  # Valor por defecto en la BD
    )
)
```

### 3. Migraciones de Datos

**Separar cambios de esquema de cambios de datos:**

```python
def upgrade():
    # Primero: cambios de esquema
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

### 4. Testing Exhaustivo

**Test en múltiples bases de datos:**

```bash
# SQLite
DATABASE_URL=sqlite:///test.db pytest tests/test_alembic_upgrade.py

# PostgreSQL
DATABASE_URL=postgresql+pg8000://user:pass@localhost/test pytest tests/test_alembic_upgrade.py

# MySQL
DATABASE_URL=mysql+mysqldb://user:pass@localhost/test pytest tests/test_alembic_upgrade.py
```

### 5. Documentación Clara

**Incluir contexto y razón de cambio:**

```python
"""Add user profile fields for enhanced user management

Revision ID: 20260125_120000
Revises: 20260120_100000
Create Date: 2026-01-25 12:00:00

This migration adds profile-related fields to support:
- User biography/about section
- Profile visibility settings
- Social media links

Breaking changes: None
Backward compatible: Yes
"""
```

### 6. Manejo de Errores

**Capturar y loggear errores apropiadamente:**

```python
def upgrade():
    try:
        op.add_column("table", sa.Column("column", sa.String(255)))
    except sa.exc.OperationalError as e:
        # La columna ya existe, continuar
        log.warning(f"Column may already exist: {e}")
```

---

## Guía Paso a Paso para Replicar

### Paso 1: Instalar Dependencias

```bash
pip install flask-alembic==3.2.0 alembic==1.18.1
```

### Paso 2: Crear Estructura de Directorios

```bash
mkdir -p app_package/migrations
touch app_package/migrations/__init__.py
```

### Paso 3: Crear Plantilla de Migración

Crear `app_package/migrations/script.py.mako` con el contenido de la plantilla mostrada arriba.

### Paso 4: Configurar Flask App

En `app_package/__init__.py`:

```python
from flask import Flask
from flask_alembic import Alembic

alembic = Alembic()

def create_app():
    app = Flask(__name__)
    
    # Configurar ruta de migraciones
    from os.path import abspath, dirname, join
    migrations_dir = abspath(join(dirname(__file__), "migrations"))
    app.config["ALEMBIC"] = {"script_location": migrations_dir}
    
    # Inicializar extensiones
    from app_package.db import database
    database.init_app(app)
    alembic.init_app(app)
    
    return app

app = create_app()
```

### Paso 5: Crear Primera Migración

1. **Crear archivo manualmente** siguiendo la convención de nombres:
   ```
   app_package/migrations/20260125_120000_initial_migration.py
   ```

2. **O usar generación automática** (requiere configuración adicional de alembic.ini):
   ```bash
   flask alembic revision -m "initial migration"
   ```

### Paso 6: Implementar upgrade() y downgrade()

```python
def upgrade():
    # Verificar y crear tablas/columnas necesarias
    pass

def downgrade():
    # Revertir cambios si es necesario
    pass
```

### Paso 7: Añadir Comandos CLI

En `app_package/cli.py`, añadir comandos para inicializar y migrar la BD.

### Paso 8: Configurar Auto-Migración (Opcional)

Implementar lógica en `init_app()` para ejecutar `alembic.upgrade()` automáticamente.

### Paso 9: Crear Tests

Implementar `tests/test_alembic_upgrade.py` basado en el ejemplo proporcionado.

### Paso 10: Documentar

Crear documentación específica del proyecto explicando:
- Cómo crear nuevas migraciones
- Cómo ejecutar migraciones
- Cómo revertir cambios
- Convenciones del proyecto

---

## Resumen de Puntos Clave

1. **Ubicación de Migraciones**: Dentro del paquete de la aplicación para distribución
2. **Configuración Explícita**: Establecer `ALEMBIC.script_location` con ruta absoluta
3. **Inicialización**: Llamar `alembic.init_app(app)` después de `database.init_app(app)`
4. **Migraciones Idempotentes**: Verificar existencia antes de crear/modificar
5. **Valores por Defecto**: Establecer `server_default` para columnas NOT NULL
6. **CLI Integration**: Exponer comandos a través de Flask CLI
7. **Auto-Migración Opcional**: Variable de entorno para control de migraciones automáticas
8. **Testing Robusto**: Test completo del ciclo upgrade → downgrade → upgrade
9. **Multi-DB Support**: Probar en SQLite, PostgreSQL y MySQL
10. **Documentación Clara**: Explicar el propósito de cada migración

---

## Recursos Adicionales

- [Documentación oficial de Alembic](https://alembic.sqlalchemy.org/)
- [Documentación de flask-alembic](https://github.com/davidism/flask-alembic)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [NOW LMS Repository](https://github.com/bmosoluciones/now-lms)

---

## Contacto y Soporte

Para preguntas o soporte sobre esta implementación:
- GitHub Issues: https://github.com/bmosoluciones/now-lms/issues
- Gitter Chat: https://gitter.im/now-lms/community

---

*Documento creado: 2026-01-25*  
*Versión NOW LMS: 1.0.0+*  
*flask-alembic: 3.2.0*  
*alembic: 1.18.1*
