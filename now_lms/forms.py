# Copyright 2022 BMO Soluciones, S.A.
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
#
# Contributors:
# - William José Moreno Reyes

"""Definición de formularios."""
# Libreria standar:

# Librerias de terceros:
from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, DateField, IntegerField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired

# pylint: disable=R0903

# Recursos locales:


# < --------------------------------------------------------------------------------------------- >
# Definición de formularios
class LoginForm(FlaskForm):
    """Formulario de inicio de sesión."""

    usuario = StringField(validators=[DataRequired()])
    acceso = PasswordField(validators=[DataRequired()])
    inicio_sesion = SubmitField()


class LogonForm(FlaskForm):
    """Formulario para crear un nuevo usuario."""

    usuario = StringField(validators=[DataRequired()])
    acceso = PasswordField(validators=[DataRequired()])
    nombre = StringField(validators=[DataRequired()])
    apellido = StringField(validators=[DataRequired()])
    correo_electronico = StringField(validators=[DataRequired()])


class CurseForm(FlaskForm):
    """Formulario para crear un nuevo curso."""

    nombre = StringField(validators=[DataRequired()])
    codigo = StringField(validators=[DataRequired()])
    descripcion = StringField(validators=[DataRequired()])
    publico = BooleanField(validators=[])
    auditable = BooleanField(validators=[])
    certificado = BooleanField(validators=[])
    precio = DecimalField(validators=[])
    capacidad = IntegerField(validators=[])
    fecha_inicio = DateField(validators=[])
    fecha_fin = DateField(validators=[])
    duracion = IntegerField(validators=[])
    nivel = SelectField("User", choices=[(0, "Introductorio"), (1, "Principiante"), (2, "Intermedio"), (2, "Avanzado")])


class CursoRecursoForm(FlaskForm):
    """Formulario para crear un nuevo recurso."""

    tipo = SelectField(
        "Tipo",
        choices=[("link", "Vinculo"), ("youtube", "Vídeo en YouTube"), ("file", "Archivo"), ("text", "Texto")],
    )


class CursoSeccionForm(FlaskForm):
    """Formulario para crear una nueva sección."""

    nombre = StringField(validators=[DataRequired()])
    descripcion = StringField(validators=[DataRequired()])


class CursoRecursoVideoYoutube(FlaskForm):
    """Formulario para un nuevo recurso Youtube."""

    nombre = StringField(validators=[DataRequired()])
    descripcion = StringField(validators=[DataRequired()])
    youtube_url = StringField(validators=[DataRequired()])


class CursoRecursoArchivoPDF(FlaskForm):
    """Formulario para un nuevo recurso PDF."""

    nombre = StringField(validators=[DataRequired()])
    descripcion = StringField(validators=[DataRequired()])


class CursoRecursoArchivoAudio(FlaskForm):
    """Formulario para un nuevo recurso de audio."""

    nombre = StringField(validators=[DataRequired()])
    descripcion = StringField(validators=[DataRequired()])


class CursoRecursoArchivoImagen(FlaskForm):
    """Formulario para un nuevo recurso de audio."""

    nombre = StringField(validators=[DataRequired()])
    descripcion = StringField(validators=[DataRequired()])
