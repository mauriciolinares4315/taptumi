"""
Panel de super-administrador. Protegido con clave maestra (.env).
"""
import hmac
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import (
    Blueprint, render_template, request, jsonify,
    session, redirect, url_for,
)

from app.config import config
from app.db import get_db
from app.security import hash_password

superadmin_bp = Blueprint("superadmin", __name__, url_prefix="/superadmin")


# ---------- Autenticación ----------

def _check_master_password(candidate: str) -> bool:
    expected = config.MASTER_PASSWORD
    if not expected or not candidate:
        return False
    return hmac.compare_digest(candidate, expected)


def superadmin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("es_superadmin"):
            if request.path.startswith("/superadmin/api/"):
                return jsonify({"error": "No autorizado"}), 401
            return redirect(url_for("superadmin.login"))
        return view(*args, **kwargs)
    return wrapped


# ---------- Vistas ----------

@superadmin_bp.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        candidate = request.form.get("master_password", "")
        if _check_master_password(candidate):
            session["es_superadmin"] = True
            return redirect(url_for("superadmin.panel"))
        error = "Clave incorrecta"
    return render_template("superadmin_login.html", error=error)


@superadmin_bp.route("/logout")
def logout():
    session.pop("es_superadmin", None)
    return redirect(url_for("superadmin.login"))


@superadmin_bp.route("/panel")
@superadmin_required
def panel():
    return render_template("superadmin_panel.html")


# ---------- API ----------

@superadmin_bp.route("/api/profiles", methods=["GET"])
@superadmin_required
def list_profiles():
    """Lista todos los perfiles con su estado."""
    db = get_db()
    try:
        cursor = db.execute(
            """SELECT slug, name, email, failed_attempts, locked_until
               FROM profiles ORDER BY name COLLATE NOCASE"""
        )
        rows = db.fetchall(cursor)   # ← el wrapper espera el cursor como argumento

        ahora = datetime.now(timezone.utc)
        perfiles = []
        for row in rows:
            # TursoRow soporta indexación [0], [1]... y también row["nombre"]
            slug = row[0]
            name = row[1]
            email = row[2]
            failed = row[3]
            locked_until = row[4]

            bloqueado = False
            restante = 0
            if locked_until:
                try:
                    lock_dt = datetime.fromisoformat(locked_until)
                    if lock_dt > ahora:
                        bloqueado = True
                        restante = int((lock_dt - ahora).total_seconds())
                except (ValueError, TypeError):
                    pass

            perfiles.append({
                "slug": slug,
                "name": name,
                "email": email or "",
                "failed_attempts": failed or 0,
                "locked": bloqueado,
                "retry_after": restante,
            })
        return jsonify({"profiles": perfiles})
    finally:
        db.close()

@superadmin_bp.route("/api/profiles/<slug>/password", methods=["POST"])
@superadmin_required
def change_password(slug):
    """Cambia la contraseña de un perfil sin necesitar la vieja."""
    data = request.get_json(silent=True) or {}
    nueva = (data.get("new_password") or "").strip()

    if len(nueva) < 6:
        return jsonify({"error": "Mínimo 6 caracteres"}), 400

    db = get_db()
    try:
        row = db.fetchone(db.execute("SELECT 1 FROM profiles WHERE slug = ?", (slug,)))
        if not row:
            return jsonify({"error": "Perfil no encontrado"}), 404

        db.execute(
            "UPDATE profiles SET password = ?, failed_attempts = 0, locked_until = NULL WHERE slug = ?",
            (hash_password(nueva), slug),
        )
        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()


@superadmin_bp.route("/api/profiles/<slug>/unlock", methods=["POST"])
@superadmin_required
def unlock_profile(slug):
    db = get_db()
    try:
        db.execute(
            "UPDATE profiles SET failed_attempts = 0, locked_until = NULL WHERE slug = ?",
            (slug,),
        )
        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()


@superadmin_bp.route("/api/profiles/<slug>/lock", methods=["POST"])
@superadmin_required
def lock_profile(slug):
    """Bloqueo manual (24 horas)."""
    hasta = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    db = get_db()
    try:
        db.execute(
            "UPDATE profiles SET locked_until = ? WHERE slug = ?",
            (hasta, slug),
        )
        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()
        
@superadmin_bp.route("/api/reset-requests", methods=["GET"])
@superadmin_required
def list_reset_requests():
    """Solicitudes de reset pendientes."""
    db = get_db()
    try:
        cur = db.execute(
            """SELECT id, slug, name, contact, message, created_at
               FROM password_reset_requests
               WHERE resolved = 0
               ORDER BY created_at DESC"""
        )
        rows = db.fetchall(cur)
        return jsonify({"requests": [
            {
                "id": row[0],
                "slug": row[1],
                "name": row[2],
                "contact": row[3],
                "message": row[4] or "",
                "created_at": row[5] or "",
            }
            for row in rows
        ]})
    finally:
        db.close()


@superadmin_bp.route("/api/reset-requests/<int:req_id>/resolve", methods=["POST"])
@superadmin_required
def resolve_reset_request(req_id):
    db = get_db()
    try:
        db.execute("UPDATE password_reset_requests SET resolved = 1 WHERE id = ?", (req_id,))
        db.commit()
        return jsonify({"success": True})
    finally:
        db.close()
