# Gestión del Footer Editable

## Descripción General

El sistema NOW LMS ahora cuenta con un footer completamente personalizable desde el panel de administración. Los administradores pueden gestionar tres secciones del pie de página:

1. **Acerca de**: Páginas estáticas configurables
2. **Enlaces Útiles**: Enlaces personalizados
3. **Síguenos**: Redes sociales (ya implementado previamente)

## Características Implementadas

### 1. Tabla de Base de Datos: EnlacesUtiles

Nueva tabla para almacenar enlaces personalizados:

```python
class EnlacesUtiles(database.Model, BaseTabla):
    titulo = database.Column(database.String(100), nullable=False)
    url = database.Column(database.String(500), nullable=False)
    orden = database.Column(database.Integer(), default=0, nullable=False)
    activo = database.Column(database.Boolean(), default=True, nullable=False)
```

### 2. Modificación a StaticPage

Se agregó el campo `mostrar_en_footer` para controlar qué páginas estáticas aparecen en el footer:

```python
class StaticPage(database.Model, BaseTabla):
    # ... campos existentes ...
    mostrar_en_footer = database.Column(database.Boolean(), default=False, nullable=False)
```

### 3. Rutas de Administración

Nuevas rutas disponibles:

- `GET /admin/enlaces-utiles` - Lista todos los enlaces útiles
- `GET/POST /admin/enlaces-utiles/new` - Crear nuevo enlace
- `GET/POST /admin/enlaces-utiles/<id>/edit` - Editar enlace existente
- `POST /admin/enlaces-utiles/<id>/delete` - Eliminar enlace

## Guía de Uso para Administradores

### Acceso al Panel de Gestión

1. Iniciar sesión como administrador
2. Ir a **Configuración** en el menú principal
3. Expandir la sección **"Gestión del Footer"** (colapsable)

### Configurar Páginas Estáticas en el Footer

1. Click en **"Gestionar Páginas Estáticas"**
2. Seleccionar la página a editar
3. Activar la casilla **"Mostrar en el footer del sitio"**
4. Guardar cambios

Las páginas activadas aparecerán automáticamente en la sección "Acerca de" del footer.

### Gestionar Enlaces Útiles

#### Crear un Nuevo Enlace

1. Click en **"Gestionar Enlaces Útiles"**
2. Click en **"Nuevo Enlace"**
3. Completar el formulario:
   - **Título del enlace**: Texto que se mostrará (max 100 caracteres)
   - **URL**: Dirección completa del enlace (max 500 caracteres)
   - **Orden**: Número para ordenar los enlaces (menor número = primero)
   - **Activo**: Marcar para que el enlace sea visible
4. Click en **"Crear Enlace"**

#### Editar un Enlace Existente

1. En la lista de enlaces útiles, click en el botón **editar** (icono lápiz)
2. Modificar los campos necesarios
3. Click en **"Guardar Cambios"**

#### Eliminar un Enlace

1. En la lista de enlaces útiles, click en el botón **eliminar** (icono papelera)
2. Confirmar la eliminación

## Estructura del Footer

El footer se divide en tres columnas:

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  ┌──────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Acerca de    │  │ Enlaces Útiles  │  │ Síguenos        │ │
│  │              │  │                 │  │                 │ │
│  │ • Página 1   │  │ • Enlace 1      │  │ 🔗 Facebook     │ │
│  │ • Página 2   │  │ • Enlace 2      │  │ 🔗 Twitter      │ │
│  │ • Página 3   │  │ • Enlace 3      │  │ 🔗 LinkedIn     │ │
│  │              │  │                 │  │ 🔗 YouTube      │ │
│  └──────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                              │
│  Copyright © 2026 Sitio. Todos los derechos reservados.     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Comportamiento por Defecto

### Si no hay páginas estáticas configuradas

La sección "Acerca de" mostrará el texto por defecto:
"Sistema de gestión de aprendizaje moderno y completo."

### Si no hay enlaces útiles configurados

La sección "Enlaces Útiles" mostrará el enlace por defecto:
- Contacto (link a `/contact`)

### Redes Sociales

Solo se mostrarán los iconos de las redes sociales que tengan URL configurada en:
**Configuración → Redes Sociales**

## Optimización y Caché

Las consultas al footer están optimizadas con caché de 300 segundos (5 minutos):

- `get_footer_pages()`: Páginas estáticas con mostrar_en_footer=True
- `get_footer_enlaces()`: Enlaces útiles activos

Esto reduce la carga en la base de datos y mejora el rendimiento del sitio.

## Consideraciones de Seguridad

- Las URLs de enlaces útiles deben incluir el protocolo completo (http:// o https://)
- Los enlaces externos se abren en una nueva pestaña con `target="_blank" rel="noopener noreferrer"`
- Validación de longitud máxima en formularios
- Solo administradores pueden gestionar el contenido del footer

## Migración de Base de Datos

La migración `20260110_150324_add_footer_customization.py` incluye:

1. Creación de la tabla `enlaces_utiles`
2. Adición del campo `mostrar_en_footer` a la tabla `static_pages`

La migración es reversible (incluye funciones `upgrade()` y `downgrade()`).

## Soporte Multi-Tema

Los cambios se aplicaron a todos los temas disponibles:

- now_lms (predeterminado)
- classic
- cambridge
- ocean
- corporative
- modern
- invest
- oxford
- amber
- sakura
- golden
- excel
- harvard

Todos los temas usan el mismo template de footer dinámico.

## Ejemplo de Uso

### Caso 1: Sitio Corporativo

**Acerca de:**
- Sobre Nosotros
- Misión y Visión
- Equipo

**Enlaces Útiles:**
- Blog Corporativo
- Centro de Ayuda
- Términos y Condiciones
- Política de Privacidad

### Caso 2: Academia en Línea

**Acerca de:**
- Acerca de la Academia
- Metodología de Enseñanza

**Enlaces Útiles:**
- Catálogo de Cursos
- Preguntas Frecuentes
- Soporte Técnico
- Certificaciones

## Código de Ejemplo

### Crear enlaces útiles programáticamente

```python
from now_lms.db import EnlacesUtiles, database

# Crear nuevo enlace
enlace = EnlacesUtiles(
    titulo="Blog de la Empresa",
    url="https://example.com/blog",
    orden=1,
    activo=True
)
database.session.add(enlace)
database.session.commit()
```

### Configurar página estática para footer

```python
from now_lms.db import StaticPage, database

# Obtener y configurar página
page = database.session.get(StaticPage, page_id)
page.mostrar_en_footer = True
database.session.commit()
```

## Troubleshooting

### Los cambios no se reflejan en el footer

- Verificar que el enlace/página esté marcado como **activo**
- Limpiar el caché del navegador
- El caché del servidor se limpia automáticamente después de 5 minutos

### Error al guardar enlaces

- Verificar que la URL incluya `http://` o `https://`
- Verificar que no se exceda la longitud máxima (título: 100 chars, URL: 500 chars)

### La sección del footer no aparece

- Verificar en Configuración que **"Mostrar pie de página en páginas públicas"** esté activado
