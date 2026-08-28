"""Rutas publicas: lo que ve cualquier persona que escanea el tag NFC."""
from flask import Blueprint, render_template, request

from app.db import get_db
from app.utils import attach_social_icon

public_bp = Blueprint("public", __name__)


@public_bp.route("/c/<slug>")
def profile(slug):
    """Pagina publica del perfil."""
    db = get_db()
    profile_row = db.fetchone(db.execute("SELECT * FROM profiles WHERE slug = ?", (slug,)))

    if not profile_row:
        db.close()
        return render_template("404.html"), 404

    # Registrar el escaneo (best-effort, no debe tumbar la pagina si falla).
    db.execute(
        """
        INSERT INTO stats (slug, ip_address, user_agent)
        VALUES (?, ?, ?)
        """,
        (slug, request.remote_addr, str(request.user_agent)[:200]),
    )
    db.commit()

    links_raw = db.fetchall(
        db.execute(
            "SELECT * FROM social_links WHERE profile_id = ? ORDER BY sort_order",
            (profile_row[0],),
        )
    )
    links = [attach_social_icon(dict(link)) for link in links_raw]

    gallery = db.fetchall(
        db.execute(
            "SELECT * FROM gallery WHERE profile_id = ? ORDER BY sort_order",
            (profile_row[0],),
        )
    )

    total_scans = db.fetchone(
        db.execute("SELECT COUNT(*) as count FROM stats WHERE slug = ?", (slug,))
    )[0]

    db.close()

    return render_template(
        "profile.html",
        profile=profile_row,
        links=links,
        gallery=gallery,
        total_scans=total_scans,
    )


@public_bp.app_errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404
