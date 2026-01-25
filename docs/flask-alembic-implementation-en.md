# flask-alembic Implementation Summary in NOW LMS

This document provides a comprehensive summary of how `flask-alembic` was implemented in the NOW LMS project, including all key points needed to replicate this implementation in another Flask project.

## Table of Contents

1. [Overview](#overview)
2. [Dependencies and Requirements](#dependencies-and-requirements)
3. [File Structure](#file-structure)
4. [Application Configuration](#application-configuration)
5. [Migration Structure](#migration-structure)
6. [CLI Commands](#cli-commands)
7. [Migration Automation](#migration-automation)
8. [Testing](#testing)
9. [Best Practices](#best-practices)
10. [Step-by-Step Guide to Replicate](#step-by-step-guide-to-replicate)

---

## Overview

`flask-alembic` is a Flask extension that integrates Alembic, a database migration tool for SQLAlchemy. In NOW LMS, it is used to manage database schema changes programmatically and in a versioned manner.

**Key Benefits:**
- Version control for database schema
- Forward and backward migrations (upgrade/downgrade)
- Support for multiple databases (SQLite, PostgreSQL, MySQL)
- Seamless integration with Flask and SQLAlchemy
- Production migration automation

---

## Dependencies and Requirements

### Required Python Packages

```txt
# requirements.txt
alembic==1.18.1
flask-alembic==3.2.0
```

These are installed along with the project's main dependencies.

### Python Versions

- Python >= 3.11 (NOW LMS)
- Compatible with Python 3.8+

---

## File Structure

```
project/
├── app_package/
│   ├── __init__.py              # Flask app and extensions initialization
│   ├── migrations/              # Migrations directory
│   │   ├── script.py.mako      # Template for new migrations
│   │   ├── 20260105_145517_add_feature.py
│   │   ├── 20260109_152634_add_tables.py
│   │   └── ...
│   ├── cli.py                   # Custom CLI commands
│   └── config/
│       └── __init__.py          # Application configuration
├── tests/
│   └── test_alembic_upgrade.py  # Migration tests
├── requirements.txt
└── development.txt
```

### Migration Directory Location

**Key Point:** In NOW LMS, migrations are stored **inside the application package** (`now_lms/migrations/`), not in the project root. This allows:
- Distributing migrations with the PyPI package
- Keeping migrations versioned with code
- Facilitating deployment across different environments

---

## Application Configuration

### 1. Initialization in `__init__.py`

```python
# app_package/__init__.py

from flask import Flask
from flask_alembic import Alembic
from flask_sqlalchemy import SQLAlchemy

# Create global Alembic instance
alembic: Alembic = Alembic()
database = SQLAlchemy()

def inicializa_extenciones_terceros(flask_app: Flask) -> None:
    """Initialize third-party extensions."""
    with flask_app.app_context():
        from os.path import abspath, dirname, join

        # IMPORTANT: Configure absolute path to migrations directory
        migrations_dir = abspath(join(dirname(__file__), "migrations"))
        flask_app.config.from_mapping({
            "ALEMBIC": {
                "script_location": migrations_dir
            }
        })

        # Initialize extensions in order
        database.init_app(flask_app)
        alembic.init_app(flask_app)

def create_app(app_name="myapp", testing=False, config_overrides=None):
    """Factory function to create Flask application."""
    flask_app = Flask(app_name)
    
    # Apply base configuration
    flask_app.config.from_mapping(BASE_CONFIG)
    
    # Apply overrides if provided
    if config_overrides:
        flask_app.config.update(config_overrides)
    
    # Initialize extensions within app context
    with flask_app.app_context():
        inicializa_extenciones_terceros(flask_app)
        # ... register blueprints, etc.
    
    return flask_app

# Create main application
app = create_app()
```

### 2. Environment Variable Configuration

```python
# app_package/config/__init__.py

from os import environ

# Variable to enable auto-migrations in production
TRUE_VALUES = {"1", "true", "yes", "on", "development", "dev"}
AUTO_MIGRATE = environ.get("APP_AUTO_MIGRATE", "0").strip().lower() in TRUE_VALUES
```

### 3. Auto-Migration Logic

```python
# app_package/__init__.py

def init_app(with_examples=False, flask_app=None):
    """Helper function to initialize the application."""
    from app_package.db.tools import check_db_access, database_is_populated
    
    app_to_use = flask_app if flask_app is not None else app
    
    DB_ACCESS = check_db_access(app_to_use)
    DB_INITIALIZED = database_is_populated(app_to_use)
    
    if DB_ACCESS:
        if DB_INITIALIZED:
            # If AUTO_MIGRATE is enabled, run migrations automatically
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
            # First time: create base schema
            initial_setup(with_examples=with_examples, flask_app=app_to_use)
            return True
    
    log.warning("Could not access the database.")
    return False
```

---

## Migration Structure

### Migration Template (script.py.mako)

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

### Complete Migration Example

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
down_revision = None  # First migration
branch_labels = None
depends_on = None


def upgrade():
    """Add allow_unverified_email_login column to configuracion table."""
    # Check if column already exists before adding it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if "configuracion" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("configuracion")]
        
        if "allow_unverified_email_login" not in columns:
            # Add column with default value False for compatibility
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
    # Check if column exists before dropping it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if "configuracion" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("configuracion")]
        
        if "allow_unverified_email_login" in columns:
            op.drop_column("configuracion", "allow_unverified_email_login")
```

### Naming Convention

NOW LMS uses the format: `YYYYMMDD_HHMMSS_description.py`

**Examples:**
- `20260105_145517_add_allow_unverified_email_login.py`
- `20260109_152634_add_missing_tables.py`
- `20260110_035505_add_blog_cover_image.py`

**Advantages:**
- Automatic chronological ordering
- Easy identification of creation time
- Clear description of purpose

---

## CLI Commands

### Flask CLI Integration

```python
# app_package/cli.py

import click
from flask.cli import FlaskGroup
from app_package import alembic, app, initial_setup

@click.group(
    cls=FlaskGroup,
    create_app=lambda: app,
    help="CLI for application administration."
)
def command() -> None:
    """Command line for application administration."""
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

# Additional alembic commands available through flask-alembic:
# flask alembic upgrade    - Migrate to latest version
# flask alembic downgrade  - Rollback migrations
# flask alembic current    - Show current version
# flask alembic history    - Show migration history
# flask alembic show       - Show migration details
```

### Command Usage

```bash
# Initialize new database
lmsctl database init

# Migrate existing database
lmsctl database migrate

# Or using Flask CLI directly
flask database migrate

# flask-alembic commands
flask alembic upgrade       # Update to latest version
flask alembic downgrade -1  # Rollback one migration
flask alembic current       # View current version
flask alembic history       # View migration history
```

---

## Migration Automation

### Auto-Migration Configuration

```bash
# Environment variable to enable auto-migrations
export APP_AUTO_MIGRATE=1
```

### Auto-Migration Flow

1. Application checks if database is populated
2. If populated and `AUTO_MIGRATE=1`, executes `alembic.upgrade()`
3. If not populated, executes `initial_setup()` and marks as `head`
4. Appropriate logs for each case

**Recommended Usage:**
- ✅ Development: `AUTO_MIGRATE=1` to sync changes automatically
- ✅ Staging: `AUTO_MIGRATE=1` to test migrations
- ⚠️ Production: Preferably run migrations manually before deployment

---

## Testing

### Robust Migration Test

```python
# tests/test_alembic_upgrade.py

import os
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.pool import StaticPool


def test_alembic_upgrade_app_context(monkeypatch):
    """
    Robust and destructive Alembic migrations test.
    
    This test verifies migrations work correctly by executing:
    1. drop_all() - Remove all tables
    2. initial_setup() - Create base schema
    3. stamp('head') - Mark DB as up-to-date
    4. upgrade() - Should do nothing on freshly created DB
    5. downgrade('base') - Downgrade to migration zero
    6. upgrade() - Upgrade back to head
    
    The entire process must execute without errors.
    """
    # Respect DATABASE_URL or use SQLite in-memory
    if not os.environ.get("DATABASE_URL"):
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    
    # Create independent app in testing mode
    from app_package import create_app, alembic, initial_setup
    
    # For SQLite in-memory, keep connection alive with StaticPool
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
        
        # Step 1: Destroy all tables (destructive test)
        db.drop_all()
        db.session.commit()
        
        # Step 2: Create base schema with initial_setup
        initial_setup(with_examples=False, flask_app=app)
        db.session.commit()
        
        # Step 2.1: Mark database as up-to-date (stamp head)
        alembic.stamp("head")
        db.session.commit()
        
        # Verify stamp created alembic_version table
        version_after_stamp = db.session.execute(
            db.text("SELECT version_num FROM alembic_version")
        ).scalar()
        assert version_after_stamp is not None
        
        # Step 3: Execute upgrade - should do nothing
        alembic.upgrade()
        db.session.commit()
        
        # Verify version remains the same
        version_after_first_upgrade = db.session.execute(
            db.text("SELECT version_num FROM alembic_version")
        ).scalar()
        assert version_after_first_upgrade == version_after_stamp
        
        # Step 4: Downgrade to base (migration zero)
        alembic.downgrade("base")
        db.session.commit()
        
        # Verify no version in alembic_version
        try:
            version_after_downgrade = db.session.execute(
                db.text("SELECT version_num FROM alembic_version")
            ).scalar()
            assert version_after_downgrade is None
        except (OperationalError, ProgrammingError):
            # alembic_version table doesn't exist, which is valid
            pass
        
        # Step 5: Upgrade again to head
        alembic.upgrade()
        db.session.commit()
        
        # Verify there's now a valid version
        version_after_final_upgrade = db.session.execute(
            db.text("SELECT version_num FROM alembic_version")
        ).scalar()
        assert version_after_final_upgrade is not None
        
        # Close session explicitly
        db.session.close()
```

### Running Tests

```bash
# Specific migration test
pytest tests/test_alembic_upgrade.py -v

# Full test suite
pytest --tb=short -q --cov=app_package
```

---

## Best Practices

### 1. Idempotent Migrations

**Always check if the change already exists:**

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

**Benefits:**
- Avoids errors when re-running migrations
- Allows recovery from partial failures
- Facilitates testing and development

### 2. Default Values

**Always set appropriate default values:**

```python
op.add_column(
    "users",
    sa.Column(
        "is_active",
        sa.Boolean(),
        nullable=False,
        server_default=sa.true()  # Default value in DB
    )
)
```

### 3. Data Migrations

**Separate schema changes from data changes:**

```python
def upgrade():
    # First: schema changes
    op.add_column("users", sa.Column("full_name", sa.String(255)))
    
    # Second: data migration
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE users 
            SET full_name = first_name || ' ' || last_name
            WHERE full_name IS NULL
        """)
    )
```

### 4. Comprehensive Testing

**Test on multiple databases:**

```bash
# SQLite
DATABASE_URL=sqlite:///test.db pytest tests/test_alembic_upgrade.py

# PostgreSQL
DATABASE_URL=postgresql+pg8000://user:pass@localhost/test pytest tests/test_alembic_upgrade.py

# MySQL
DATABASE_URL=mysql+mysqldb://user:pass@localhost/test pytest tests/test_alembic_upgrade.py
```

### 5. Clear Documentation

**Include context and reason for change:**

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

### 6. Error Handling

**Capture and log errors appropriately:**

```python
def upgrade():
    try:
        op.add_column("table", sa.Column("column", sa.String(255)))
    except sa.exc.OperationalError as e:
        # Column already exists, continue
        log.warning(f"Column may already exist: {e}")
```

---

## Step-by-Step Guide to Replicate

### Step 1: Install Dependencies

```bash
pip install flask-alembic==3.2.0 alembic==1.18.1
```

### Step 2: Create Directory Structure

```bash
mkdir -p app_package/migrations
touch app_package/migrations/__init__.py
```

### Step 3: Create Migration Template

Create `app_package/migrations/script.py.mako` with the template content shown above.

### Step 4: Configure Flask App

In `app_package/__init__.py`:

```python
from flask import Flask
from flask_alembic import Alembic

alembic = Alembic()

def create_app():
    app = Flask(__name__)
    
    # Configure migrations path
    from os.path import abspath, dirname, join
    migrations_dir = abspath(join(dirname(__file__), "migrations"))
    app.config["ALEMBIC"] = {"script_location": migrations_dir}
    
    # Initialize extensions
    from app_package.db import database
    database.init_app(app)
    alembic.init_app(app)
    
    return app

app = create_app()
```

### Step 5: Create First Migration

1. **Create file manually** following naming convention:
   ```
   app_package/migrations/20260125_120000_initial_migration.py
   ```

2. **Or use automatic generation** (requires additional alembic.ini configuration):
   ```bash
   flask alembic revision -m "initial migration"
   ```

### Step 6: Implement upgrade() and downgrade()

```python
def upgrade():
    # Verify and create necessary tables/columns
    pass

def downgrade():
    # Revert changes if necessary
    pass
```

### Step 7: Add CLI Commands

In `app_package/cli.py`, add commands to initialize and migrate the DB.

### Step 8: Configure Auto-Migration (Optional)

Implement logic in `init_app()` to run `alembic.upgrade()` automatically.

### Step 9: Create Tests

Implement `tests/test_alembic_upgrade.py` based on the provided example.

### Step 10: Document

Create project-specific documentation explaining:
- How to create new migrations
- How to run migrations
- How to revert changes
- Project conventions

---

## Key Points Summary

1. **Migration Location**: Inside application package for distribution
2. **Explicit Configuration**: Set `ALEMBIC.script_location` with absolute path
3. **Initialization**: Call `alembic.init_app(app)` after `database.init_app(app)`
4. **Idempotent Migrations**: Verify existence before creating/modifying
5. **Default Values**: Set `server_default` for NOT NULL columns
6. **CLI Integration**: Expose commands through Flask CLI
7. **Optional Auto-Migration**: Environment variable for automatic migration control
8. **Robust Testing**: Complete test of upgrade → downgrade → upgrade cycle
9. **Multi-DB Support**: Test on SQLite, PostgreSQL, and MySQL
10. **Clear Documentation**: Explain the purpose of each migration

---

## Additional Resources

- [Official Alembic Documentation](https://alembic.sqlalchemy.org/)
- [flask-alembic Documentation](https://github.com/davidism/flask-alembic)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [NOW LMS Repository](https://github.com/bmosoluciones/now-lms)

---

## Contact and Support

For questions or support about this implementation:
- GitHub Issues: https://github.com/bmosoluciones/now-lms/issues
- Gitter Chat: https://gitter.im/now-lms/community

---

*Document created: 2026-01-25*  
*NOW LMS Version: 1.0.0+*  
*flask-alembic: 3.2.0*  
*alembic: 1.18.1*
