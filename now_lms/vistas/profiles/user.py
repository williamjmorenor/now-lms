# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_uploads import UploadNotAllowed
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS, images
from now_lms.db import Usuario, database
from now_lms.db.tools import elimina_imagen_usuario
from now_lms.forms import UserForm, ChangePasswordForm
from now_lms.logs import log
from now_lms.misc import GENEROS

# Constants
PROFILE_ROUTE = "/perfil"

user_profile = Blueprint("user_profile", __name__, template_folder=DIRECTORIO_PLANTILLAS)


# ---------------------------------------------------------------------------------------
# Espacio del usuario, por defecto un usuario se considera un estudiante.
# ---------------------------------------------------------------------------------------
@user_profile.route("/student")
@login_required
def pagina_estudiante():
    """Perfil de usuario."""
    return render_template("perfiles/estudiante.html")


@user_profile.route("/perfil")
@login_required
def perfil():
    """Perfil del usuario."""
    registro_usuario = database.session.execute(database.select(Usuario).filter(Usuario.id == current_user.id)).first()[0]

    return render_template("inicio/perfil.html", perfil=registro_usuario, genero=GENEROS)


@user_profile.route("/user/<id_usuario>")
@login_required
def usuario(id_usuario):
    """Acceso administrativo al perfil de un usuario."""
    perfil_usuario = database.session.query(Usuario).filter_by(usuario=id_usuario).first()
    # La misma plantilla del perfil de usuario con permisos elevados como
    # activar desactivar el perfil o cambiar el perfil del usuario.
    if current_user.usuario == id_usuario or current_user.tipo != "student" or perfil_usuario.visible is True:
        return render_template("inicio/perfil.html", perfil=perfil_usuario, genero=GENEROS)
    else:
        return render_template("inicio/private.html")


@user_profile.route("/perfil/edit/<ulid>", methods=["GET", "POST"])
@login_required
def edit_perfil(ulid: str):
    """Actualizar información de usuario."""
    if current_user.id != ulid:
        abort(403)

    usuario_ = database.session.get(Usuario, ulid)
    form = UserForm(obj=usuario_)

    if request.method == "POST":
        #
        usuario_.nombre = form.nombre.data
        usuario_.apellido = form.apellido.data
        usuario_.correo_electronico = form.correo_electronico.data
        usuario_.url = form.url.data
        usuario_.linkedin = form.linkedin.data
        usuario_.facebook = form.facebook.data
        usuario_.twitter = form.twitter.data
        usuario_.github = form.github.data
        usuario_.youtube = form.youtube.data
        usuario_.genero = form.genero.data
        usuario_.titulo = form.titulo.data
        usuario_.nacimiento = form.nacimiento.data
        usuario_.bio = form.bio.data

        if form.correo_electronico.data != usuario_.correo_electronico:
            usuario_.correo_electronico_verificado = False
            flash("Favor verifique su nuevo correo electronico.", "warning")

        try:  # pragma: no cover
            database.session.commit()
            cache.delete("view/" + url_for("perfil"))
            flash("Pefil actualizado.", "success")
            if "logo" in request.files:
                try:
                    picture_file = images.save(request.files["logo"], folder="usuarios", name=current_user.id + ".jpg")
                    if picture_file:
                        usuario_ = database.session.execute(
                            database.select(Usuario).filter(Usuario.id == current_user.id)
                        ).first()[0]
                        usuario_.portada = True
                        database.session.commit()
                        flash("Imagen de perfil actualizada.", "success")
                except UploadNotAllowed:  # pragma: no cover
                    log.warning("No se pudo actualizar la imagen de perfil.", "error")
        except OperationalError:  # pragma: no cover
            flash("Error al editar el perfil.", "error")

        return redirect(PROFILE_ROUTE)

    else:  # pragma: no cover
        return render_template("inicio/perfil_editar.html", form=form, usuario=usuario_)


@user_profile.route("/perfil/<ulid>/delete_logo")
@login_required
def elimina_logo_usuario(ulid: str):
    """Elimina logo de usuario."""
    if current_user.id != ulid:
        abort(403)

    elimina_imagen_usuario(ulid=ulid)
    return redirect(PROFILE_ROUTE)


@user_profile.route("/perfil/cambiar_contraseña/<ulid>", methods=["GET", "POST"])
@login_required
def cambiar_contraseña(ulid: str):
    """Cambiar contraseña del usuario."""
    if current_user.id != ulid:
        abort(403)

    usuario_ = database.session.get(Usuario, ulid)
    if not usuario_:
        abort(404)

    form = ChangePasswordForm()

    if request.method == "POST" and form.validate_on_submit():
        from now_lms.auth import validar_acceso, proteger_passwd

        # Verificar contraseña actual
        if not validar_acceso(usuario_.usuario, form.current_password.data):
            flash("La contraseña actual es incorrecta.", "error")
            return render_template("inicio/cambiar_contraseña.html", form=form, usuario=usuario_)

        # Verificar que las nuevas contraseñas coincidan
        if form.new_password.data != form.confirm_password.data:
            flash("Las nuevas contraseñas no coinciden.", "error")
            return render_template("inicio/cambiar_contraseña.html", form=form, usuario=usuario_)

        # Actualizar contraseña
        try:
            usuario_.acceso = proteger_passwd(form.new_password.data)
            database.session.commit()
            flash("Contraseña actualizada exitosamente.", "success")
            return redirect(PROFILE_ROUTE)
        except OperationalError:  # pragma: no cover
            flash("Error al actualizar la contraseña.", "error")

    return render_template("inicio/cambiar_contraseña.html", form=form, usuario=usuario_)
