# Copyright 2022 - 2024 BMO Soluciones, S.A.
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


"""Access control for the application."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import base64
from datetime import datetime, timedelta, timezone
from functools import wraps

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import abort, current_app, flash, url_for
from flask_login import current_user

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.db import MailConfig, Usuario, database
from now_lms.logs import log

ph = PasswordHasher()


# ---------------------------------------------------------------------------------------
# Proteger contraseñas de usuarios.
# ---------------------------------------------------------------------------------------
def proteger_passwd(clave):
    """Devuelve una contraseña salteada con argon2."""

    _hash = ph.hash(clave.encode()).encode("utf-8")

    return _hash


def validar_acceso(usuario_id, acceso):
    """Verifica el inicio de sesión del usuario."""

    log.trace(f"Verificando acceso de {usuario_id}")
    registro = database.session.query(Usuario).filter_by(usuario=usuario_id).first()

    if not registro:
        registro = database.session.query(Usuario).filter_by(correo_electronico=usuario_id).first()

    if registro is not None:
        try:
            ph.verify(registro.acceso, acceso.encode())
            clave_validada = True
        except VerifyMismatchError:
            clave_validada = False
    else:
        log.trace(f"No se encontro registro de usuario {usuario_id}")
        clave_validada = False

    log.trace(f"Resultado de validación de acceso es {clave_validada}")
    if clave_validada:
        registro.ultimo_acceso = datetime.now()
        database.session.commit()

    return clave_validada


# ---------------------------------------------------------------------------------------
# Comprobar el acceso a un perfil de acuerdo con el perfil del usuario.
# ---------------------------------------------------------------------------------------
def perfil_requerido(perfil_id):
    """Comprueba si un usuario tiene acceso a un recurso determinado en base a su tipo."""

    def decorator_verifica_acceso(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Favor iniciar sesión.", "warning")
                return abort(403)

            # Always allow admin access
            if current_user.tipo == "admin":
                return func(*args, **kwargs)

            # Handle tuple format for multiple allowed profiles
            elif isinstance(perfil_id, tuple):
                if current_user.tipo in perfil_id:
                    return func(*args, **kwargs)
            # Handle string format for single profile
            elif isinstance(perfil_id, str) and current_user.tipo == perfil_id:
                return func(*args, **kwargs)

            # Deny access if the user does not have the required profile
            else:
                flash("No se encuentra autorizado a acceder al recurso solicitado.", "error")
                return abort(403)

        return wrapper

    return decorator_verifica_acceso


# ---------------------------------------------------------------------------------------
# Evita registrar información sensible en la base de datos en texto plano.
# ---------------------------------------------------------------------------------------
def proteger_secreto(password):
    """Devuelve el hash de una contraseña."""

    with current_app.app_context():
        from now_lms.db import Configuracion, database

        config = database.session.execute(database.select(Configuracion)).first()[0]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=config.r,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(current_app.config.get("SECRET_KEY").encode()))
        f = Fernet(key)
        return f.encrypt(password.encode())


def descifrar_secreto(hash):
    """Devuelve el valor de una contraseña protegida."""

    with current_app.app_context():
        from now_lms.db import Configuracion, database

        config = database.session.execute(database.select(Configuracion)).first()[0]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=config.r,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(current_app.config.get("SECRET_KEY").encode()))
        f = Fernet(key)
        try:
            s = f.decrypt(hash)
            return s.decode()
        except:  # noqa: E722
            return None


# ---------------------------------------------------------------------------------------
# Validación de tokens de confirmación de correo electrónico.
# ---------------------------------------------------------------------------------------
def generate_confirmation_token(mail):
    expiration_time = datetime.now(timezone.utc) + timedelta(seconds=36000)
    data = {"exp": expiration_time, "confirm_id": mail}
    token = jwt.encode(data, current_app.secret_key, algorithm="HS512")
    return token


def validate_confirmation_token(token):
    try:
        data = jwt.decode(token, current_app.secret_key, algorithms=["HS512"])
        log.trace(f"Token de confirmación decodificado: {data}")
    except jwt.ExpiredSignatureError:
        log.warning("Intento de verificación expirado.")
        return False
    except jwt.InvalidSignatureError:
        log.warning("Intento de verificación invalido.")
        return False

    if data.get("confirm_id", None):
        log.trace(f"Validando token de confirmación para {data.get('confirm_id', None)}")
        user = database.session.execute(
            database.select(Usuario).filter_by(correo_electronico=data.get("confirm_id", None))
        ).first()[0]
        if user:
            log.info(f"Se ha verificado el usuario {user.usuario}, la cuenta se encuentra activa.")
            user.correo_electronico_verificado = True
            user.activo = True
            database.session.commit()
            return True
        else:
            log.warning(f"Usuario con correo {data.get('confirm_id', None)} no encontrado.")
            return False
    else:
        return False


def send_confirmation_email(user):

    from flask_mail import Message
    from now_lms.mail import send_mail

    config = database.session.execute(database.select(MailConfig)).first()[0]

    msg = Message(
        subject="Email verification",
        recipients=[user.correo_electronico],
        sender=((config.MAIL_DEFAULT_SENDER_NAME or "NOW LMS"), config.MAIL_DEFAULT_SENDER),
    )
    token = generate_confirmation_token(user.correo_electronico)
    url = url_for("user.check_mail", token=token, _external=True)
    msg.html = f"""
    <div class="container">
        <div class="header">
          <h1>Email verification</h1>
        </div>
        <div class="content">
          <p>Please confirm your email:</p>
          <p>
              <a href="{url}">{url}</a>
          </p>
        </div>
        <div class="footer">
          <p>This is an automated message. Please do not reply to this email.</p>
        </div>
      </div>
    """
    try:
        send_mail(
            msg,
            background=False,
            no_config=True,
            _log="Correo de confirmación enviado",
            _flush="Correo de confirmación enviado.",
        )
        log.info(f"Correo de confirmación enviado al usuario {user.usuario}")
    except Exception as e:  # noqa: E722
        log.warning(f"Error al enviar un correo de confirmació el usuario {user.usuario}: {e}")


# ---------------------------------------------------------------------------------------
# Password reset functionality
# ---------------------------------------------------------------------------------------
def generate_password_reset_token(email):
    """Generate a password reset token."""
    expiration_time = datetime.now(timezone.utc) + timedelta(seconds=3600)  # 1 hour expiration
    data = {"exp": expiration_time, "reset_email": email, "action": "password_reset"}
    token = jwt.encode(data, current_app.secret_key, algorithm="HS512")
    return token


def validate_password_reset_token(token):
    """Validate a password reset token and return the email if valid."""
    try:
        data = jwt.decode(token, current_app.secret_key, algorithms=["HS512"])
        log.trace(f"Token de restablecimiento decodificado: {data}")
    except jwt.ExpiredSignatureError:
        log.warning("Token de restablecimiento expirado.")
        return None
    except jwt.InvalidSignatureError:
        log.warning("Token de restablecimiento inválido.")
        return None
    except jwt.DecodeError:
        log.warning("Token de restablecimiento con formato inválido.")
        return None
    except Exception as e:
        log.warning(f"Error al validar token de restablecimiento: {e}")
        return None

    if data.get("reset_email", None) and data.get("action") == "password_reset":
        return data.get("reset_email")
    return None


def send_password_reset_email(user):
    """Send password reset email to user."""
    from flask_mail import Message
    from now_lms.mail import send_mail

    config = database.session.execute(database.select(MailConfig)).first()[0]

    msg = Message(
        subject="Recuperación de Contraseña - NOW LMS",
        recipients=[user.correo_electronico],
        sender=((config.MAIL_DEFAULT_SENDER_NAME or "NOW LMS"), config.MAIL_DEFAULT_SENDER),
    )
    token = generate_password_reset_token(user.correo_electronico)
    url = url_for("user.reset_password", token=token, _external=True)
    msg.html = f"""
    <div class="container">
        <div class="header">
          <h1>Recuperación de Contraseña</h1>
        </div>
        <div class="content">
          <p>Hola {user.nombre},</p>
          <p>Has solicitado recuperar tu contraseña. Haz clic en el siguiente enlace para establecer una nueva contraseña:</p>
          <p>
              <a href="{url}" style="background-color: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">Restablecer Contraseña</a>
          </p>
          <p>Si no puedes hacer clic en el botón, copia y pega la siguiente URL en tu navegador:</p>
          <p>{url}</p>
          <p>Este enlace expirará en 1 hora por seguridad.</p>
          <p>Si no solicitaste este cambio, puedes ignorar este correo.</p>
        </div>
        <div class="footer">
          <p>Este es un mensaje automático. Por favor no respondas a este correo.</p>
        </div>
      </div>
    """
    try:
        send_mail(
            msg,
            background=False,
            no_config=True,
            _log="Correo de recuperación de contraseña enviado",
            _flush="Correo de recuperación de contraseña enviado.",
        )
        log.info(f"Correo de recuperación enviado al usuario {user.usuario}")
        return True
    except Exception as e:  # noqa: E722
        log.warning(f"Error al enviar correo de recuperación al usuario {user.usuario}: {e}")
        return False
