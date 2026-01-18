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

"""
Test end-to-end para funcionalidad de blog.

Prueba el flujo completo de:
- Creación de posts de blog
- Edición de posts
- Visualización pública
- Comentarios
- Tags de blog
"""

import pytest

from now_lms.auth import proteger_passwd
from now_lms.db import BlogComment, BlogPost, BlogTag, Usuario, database

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


def _crear_admin(db_session) -> Usuario:
    """Crea un usuario administrador para las pruebas."""
    user = Usuario(
        usuario="admin",
        acceso=proteger_passwd("admin"),
        nombre="Admin",
        correo_electronico="admin@example.com",
        tipo="admin",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _login_admin(app):
    """Inicia sesión como administrador y retorna el cliente."""
    client = app.test_client()
    resp = client.post("/user/login", data={"usuario": "admin", "acceso": "admin"}, follow_redirects=False)
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    return client


def test_e2e_blog_post_creation_and_viewing(app, db_session):
    """Test: crear un post de blog y visualizarlo públicamente."""
    # 1) Crear admin y login
    _crear_admin(db_session)
    client = _login_admin(app)

    # 2) Crear post de blog via POST
    resp_new = client.post(
        "/blog/admin/new",
        data={
            "title": "Mi Primer Post",
            "content": "Este es el contenido del post",
            "excerpt": "Resumen corto",
            "status": "published",
        },
        follow_redirects=False,
    )
    assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}

    # 3) Verificar que el post existe en la base de datos
    post = db_session.execute(database.select(BlogPost).filter_by(title="Mi Primer Post")).scalars().first()
    assert post is not None
    assert post.content == "Este es el contenido del post"
    assert post.status == "published"
    assert post.slug is not None

    # 4) Visualizar el post públicamente (sin login)
    client_public = app.test_client()
    resp_view = client_public.get(f"/blog/{post.slug}")
    assert resp_view.status_code == 200
    assert b"Mi Primer Post" in resp_view.data

    # 5) Verificar que el post aparece en el índice del blog
    resp_index = client_public.get("/blog")
    assert resp_index.status_code == 200
    assert b"Mi Primer Post" in resp_index.data


def test_e2e_blog_post_editing(app, db_session):
    """Test: editar un post de blog existente."""
    # 1) Crear admin y login
    admin = _crear_admin(db_session)
    client = _login_admin(app)

    # 2) Crear post inicial
    post = BlogPost(
        title="Post Original",
        content="Contenido original",
        excerpt="Resumen original",
        status="published",
        slug="post-original",
        author_id=admin.id,
    )
    db_session.add(post)
    db_session.commit()
    post_id = post.id

    # 3) Editar el post via POST
    resp_edit = client.post(
        f"/blog/admin/{post_id}/edit",
        data={
            "title": "Post Editado",
            "content": "Contenido editado",
            "excerpt": "Resumen editado",
            "status": "published",
        },
        follow_redirects=False,
    )
    assert resp_edit.status_code in REDIRECT_STATUS_CODES | {200}

    # 4) Verificar cambios en la base de datos
    post_editado = db_session.get(BlogPost, post_id)
    assert post_editado is not None
    assert post_editado.title == "Post Editado"
    assert post_editado.content == "Contenido editado"
    assert post_editado.excerpt == "Resumen editado"


def test_e2e_blog_comments(app, db_session):
    """Test: agregar comentarios a un post de blog."""
    # 1) Crear admin y post
    admin = _crear_admin(db_session)
    post = BlogPost(
        title="Post con Comentarios",
        content="Contenido del post",
        excerpt="Resumen",
        status="published",
        slug="post-con-comentarios",
        author_id=admin.id,
    )
    db_session.add(post)
    db_session.commit()
    post_id = post.id

    # 2) Login como admin
    client = _login_admin(app)

    # 3) Agregar comentario via POST
    resp_comment = client.post(
        f"/blog/{post.slug}/comment",
        data={
            "content": "Este es un comentario de prueba",
        },
        follow_redirects=False,
    )
    assert resp_comment.status_code in REDIRECT_STATUS_CODES | {200}

    # 4) Verificar que el comentario existe en la base de datos
    comentario = (
        db_session.execute(database.select(BlogComment).filter_by(post_id=post_id)).scalars().first()
    )
    assert comentario is not None
    assert comentario.content == "Este es un comentario de prueba"
    assert comentario.author_id == admin.id


def test_e2e_blog_tags(app, db_session):
    """Test: crear y usar tags de blog."""
    # 1) Crear admin y login
    admin = _crear_admin(db_session)
    client = _login_admin(app)

    # 2) Crear tag de blog via POST
    resp_new_tag = client.post(
        "/blog/admin/tag/new",
        data={
            "name": "Python",
            "description": "Posts sobre Python",
        },
        follow_redirects=False,
    )
    assert resp_new_tag.status_code in REDIRECT_STATUS_CODES | {200}

    # 3) Verificar que el tag existe en la base de datos
    tag = db_session.execute(database.select(BlogTag).filter_by(name="Python")).scalars().first()
    assert tag is not None
    assert tag.slug is not None

    # 4) Crear post con el tag
    resp_new_post = client.post(
        "/blog/admin/new",
        data={
            "title": "Post sobre Python",
            "content": "Contenido sobre Python",
            "excerpt": "Resumen",
            "status": "published",
            "tags": [str(tag.id)],
        },
        follow_redirects=False,
    )
    assert resp_new_post.status_code in REDIRECT_STATUS_CODES | {200}

    # 5) Verificar que el post tiene el tag asignado
    post = (
        db_session.execute(database.select(BlogPost).filter_by(title="Post sobre Python")).scalars().first()
    )
    assert post is not None
    # Verificar relación con tags (si existe)
    if hasattr(post, "tags"):
        assert tag in post.tags


def test_e2e_blog_draft_post(app, db_session):
    """Test: crear un post como draft y verificar que no es visible públicamente."""
    # 1) Crear admin y login
    admin = _crear_admin(db_session)
    client = _login_admin(app)

    # 2) Crear post como draft
    resp_new = client.post(
        "/blog/admin/new",
        data={
            "title": "Post Draft",
            "content": "Este post es un borrador",
            "excerpt": "Resumen",
            "status": "draft",
        },
        follow_redirects=False,
    )
    assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}

    # 3) Verificar que el post existe como draft en la base de datos
    post = db_session.execute(database.select(BlogPost).filter_by(title="Post Draft")).scalars().first()
    assert post is not None
    assert post.status == "draft"

    # 4) Verificar que NO aparece en el índice público
    client_public = app.test_client()
    resp_index = client_public.get("/blog")
    assert resp_index.status_code == 200
    assert b"Post Draft" not in resp_index.data


def test_e2e_blog_post_list_admin(app, db_session):
    """Test: listar posts desde el panel de administración."""
    # 1) Crear admin y login
    admin = _crear_admin(db_session)
    client = _login_admin(app)

    # 2) Crear varios posts
    for i in range(3):
        post = BlogPost(
            title=f"Post {i}",
            content=f"Contenido {i}",
            excerpt=f"Resumen {i}",
            status="published",
            slug=f"post-{i}",
            author_id=admin.id,
        )
        db_session.add(post)
    db_session.commit()

    # 3) Ver lista de posts en admin
    resp_list = client.get("/blog/admin")
    assert resp_list.status_code == 200
    assert b"Post 0" in resp_list.data
    assert b"Post 1" in resp_list.data
    assert b"Post 2" in resp_list.data
