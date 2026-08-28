"""
Rutas de administracion:
- /admin/<slug>          panel de edicion de un perfil existente
- /create                formulario para crear un perfil nuevo (protegido)
- /create/access [POST]  valida la contrasena maestra y abre sesion
"""
from flask import Blueprint, jsonify, render_template, request, session

from app.config import config
from app.extensions import limiter
from app.security import verify_master_password

admin_bp = Blueprint("admin", __name__)

SESSION_KEY = "create_access_granted"


@admin_bp.route("/admin/<slug>")
def panel(slug):
    """Panel de administracion de un perfil (la contrasena se valida via API)."""
    return render_template("admin.html", slug=slug)


@admin_bp.route("/create")
def create_profile_page():
    """
    Formulario para crear un perfil nuevo.

    El acceso se controla por sesion (ver /create/access), nunca por un
    token en la URL: un token en la querystring queda guardado en el
    historial del navegador, en logs del servidor y se filtra por el
    header Referer si la pagina carga cualquier recurso externo.
    """
    if session.get(SESSION_KEY):
        return render_template("create_profile.html")
    return render_template("create_login.html")


@admin_bp.route("/create/access", methods=["POST"])
@limiter.limit(config.RATELIMIT_LOGIN)
def create_access():
    """Valida la contrasena maestra y, si es correcta, abre la sesion."""
    data = request.get_json(silent=True) or {}
    candidate = data.get("master_password", "")

    if not verify_master_password(candidate, config.MASTER_PASSWORD):
        return jsonify({"valid": False, "error": "Contrasena incorrecta"}), 401

    session[SESSION_KEY] = True
    session.permanent = False
    return jsonify({"valid": True})
