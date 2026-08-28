"""Rutas API (JSON) consumidas por los templates via fetch()."""
import uuid
import os

from flask import Blueprint, jsonify, request, session

from app.config import config
from app.db import get_db
from app.extensions import limiter
from app.security import (
    clean_slug,
    hash_password,
    is_legacy_plaintext,
    verify_password,
)
from app.utils import allowed_file

try:
    import cloudinary
    import cloudinary.uploader

    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

if CLOUDINARY_AVAILABLE:
    cloudinary.config(
        cloud_name=config.CLOUDINARY_CLOUD_NAME,
        api_key=config.CLOUDINARY_API_KEY,
        api_secret=config.CLOUDINARY_API_SECRET,
        secure=True,
    )

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _profile_password_matches(slug: str, candidate_password: str) -> bool:
    """Confirma que candidate_password corresponde al perfil `slug`, migrando
    contrasenas viejas en texto plano a hash sobre la marcha si aplica."""
    if not slug or not candidate_password:
        return False

    db = get_db()
    row = db.fetchone(db.execute("SELECT password FROM profiles WHERE slug = ?", (slug,)))
    if not row:
        db.close()
        return False

    stored = row[0]
    ok = verify_password(candidate_password, stored)

    if ok and is_legacy_plaintext(stored):
        db.execute(
            "UPDATE profiles SET password = ? WHERE slug = ?",
            (hash_password(candidate_password), slug),
        )
        db.commit()

    db.close()
    return ok


@api_bp.route("/profile/<slug>")
def get_profile(slug):
    """Obtener perfil como JSON (datos publicos, no incluye password)."""
    db = get_db()
    profile = db.fetchone(db.execute("SELECT * FROM profiles WHERE slug = ?", (slug,)))

    if not profile:
        db.close()
        return jsonify({"error": "Perfil no encontrado"}), 404

    links = db.fetchall(
        db.execute(
            "SELECT platform, url, label, icon FROM social_links WHERE profile_id = ? ORDER BY sort_order",
            (profile[0],),
        )
    )
    gallery = db.fetchall(
        db.execute(
            "SELECT image_url, caption FROM gallery WHERE profile_id = ? ORDER BY sort_order",
            (profile[0],),
        )
    )
    db.close()

    return jsonify(
        {
            "slug": profile[1],
            "name": profile[2],
            "role": profile[3],
            "company": profile[4],
            "bio": profile[5],
            "whatsapp": profile[6],
            "email": profile[7],
            "phone": profile[8],
            "photo_url": profile[9],
            "theme_color": profile[11],
            "links": [dict(link) for link in links],
            "gallery": [dict(img) for img in gallery],
        }
    )


@api_bp.route("/validate-password/<slug>", methods=["POST"])
@limiter.limit(config.RATELIMIT_LOGIN)
def validate_password(slug):
    """Validar la contrasena de administracion de un perfil."""
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")

    if _profile_password_matches(slug, password):
        return jsonify({"valid": True}), 200
    return jsonify({"valid": False, "error": "Contrasena incorrecta"}), 401


@api_bp.route("/profile/<slug>", methods=["POST"])
@limiter.limit(config.RATELIMIT_LOGIN)
def update_profile(slug):
    """Actualizar un perfil existente (requiere su contrasena)."""
    data = request.get_json(silent=True) or {}

    db = get_db()
    profile = db.fetchone(db.execute("SELECT * FROM profiles WHERE slug = ?", (slug,)))
    if not profile:
        db.close()
        return jsonify({"error": "Perfil no encontrado"}), 404
    db.close()

    if not _profile_password_matches(slug, data.get("password", "")):
        return jsonify({"error": "Contrasena incorrecta"}), 401

    db = get_db()
    db.execute(
        """
        UPDATE profiles SET
            name = ?, role = ?, company = ?, bio = ?,
            whatsapp = ?, email = ?, phone = ?, photo_url = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE slug = ?
        """,
        (
            data.get("name", profile[2]),
            data.get("role", profile[3]),
            data.get("company", profile[4]),
            data.get("bio", profile[5]),
            data.get("whatsapp", profile[6]),
            data.get("email", profile[7]),
            data.get("phone", profile[8]),
            data.get("photo_url", profile[9]),
            slug,
        ),
    )

    if "links" in data:
        db.execute("DELETE FROM social_links WHERE profile_id = ?", (profile[0],))
        for i, link in enumerate(data["links"]):
            db.execute(
                """
                INSERT INTO social_links (profile_id, platform, url, label, icon, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (profile[0], link["platform"], link["url"], link["label"], link.get("icon", "link"), i),
            )

    if "gallery" in data:
        db.execute("DELETE FROM gallery WHERE profile_id = ?", (profile[0],))
        for i, img in enumerate(data["gallery"][:4]):
            db.execute(
                """
                INSERT INTO gallery (profile_id, image_url, caption, sort_order)
                VALUES (?, ?, ?, ?)
                """,
                (profile[0], img["image_url"], img.get("caption", ""), i),
            )

    db.commit()
    db.close()

    return jsonify({"success": True, "message": "Perfil actualizado"})


@api_bp.route("/stats/<slug>")
def get_stats(slug):
    """Obtener estadisticas de escaneos de un perfil."""
    db = get_db()
    total = db.fetchone(db.execute("SELECT COUNT(*) as count FROM stats WHERE slug = ?", (slug,)))[0]
    daily = db.fetchall(
        db.execute(
            """
            SELECT DATE(scanned_at) as date, COUNT(*) as count
            FROM stats
            WHERE slug = ? AND scanned_at >= date('now', '-30 days')
            GROUP BY DATE(scanned_at)
            ORDER BY date
            """,
            (slug,),
        )
    )
    db.close()

    return jsonify({"total_scans": total, "daily_scans": [dict(row) for row in daily]})


@api_bp.route("/create-profile", methods=["POST"])
@limiter.limit(config.RATELIMIT_CREATE)
def create_profile():
    """Crear un nuevo perfil (requiere haber pasado por /create con la sesion abierta)."""
    if not session.get("create_access_granted"):
        return jsonify({"error": "No autorizado. Vuelve a /create e inicia sesion."}), 401

    data = request.get_json(silent=True) or {}

    slug = clean_slug(data.get("slug", ""))
    name = data.get("name", "").strip()
    password = data.get("password", "")

    if not slug:
        return jsonify({"error": "El slug es obligatorio"}), 400
    if not name:
        return jsonify({"error": "El nombre es obligatorio"}), 400
    if len(password) < 6:
        return jsonify({"error": "La contrasena debe tener al menos 6 caracteres"}), 400

    db = get_db()
    existing = db.fetchone(db.execute("SELECT id FROM profiles WHERE slug = ?", (slug,)))
    if existing:
        db.close()
        return jsonify({"error": f'El slug "{slug}" ya esta en uso. Elige otro.'}), 400

    try:
        db.execute(
            """
            INSERT INTO profiles (slug, name, role, company, bio, whatsapp, email, phone, photo_url, password, theme_color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slug,
                name,
                data.get("role", ""),
                data.get("company", ""),
                "",
                data.get("whatsapp", ""),
                data.get("email", ""),
                data.get("phone", ""),
                data.get("photo_url", ""),
                hash_password(password),
                "#1a1a2e",
            ),
        )
        db.commit()
        db.close()

        return jsonify(
            {
                "success": True,
                "slug": slug,
                "public_url": f"/c/{slug}",
                "admin_url": f"/admin/{slug}",
            }
        )
    except Exception as e:
        db.close()
        return jsonify({"error": f"Error al crear perfil: {e}"}), 500


@api_bp.route("/upload", methods=["POST"])
@limiter.limit("20 per minute")
def upload_image():
    """
    Subir una imagen (Cloudinary si esta configurado, si no, disco local).

    Requiere estar autorizado: o bien la sesion de creacion de perfil
    abierta (/create), o bien la contrasena del perfil que se esta
    editando (slug + password en el form-data).
    """
    authorized = session.get("create_access_granted") or _profile_password_matches(
        request.form.get("slug", ""), request.form.get("password", "")
    )
    if not authorized:
        return jsonify({"error": "No autorizado"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No filename"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Tipo de archivo no permitido"}), 400

    if CLOUDINARY_AVAILABLE and config.CLOUDINARY_CLOUD_NAME:
        try:
            result = cloudinary.uploader.upload(
                file,
                folder="nfc-profiles",
                transformation=[
                    {"width": 1200, "height": 1200, "crop": "limit"},
                    {"quality": "auto", "fetch_format": "auto"},
                ],
            )
            return jsonify({"url": result["secure_url"], "public_id": result["public_id"]})
        except Exception as e:
            # No tumbamos la subida: caemos al fallback local, pero
            # dejamos rastro del error real en los logs del servidor.
            print(f"[upload] Cloudinary fallo, usando fallback local: {e}")

    filename = f"{uuid.uuid4()}_{file.filename}"
    from werkzeug.utils import secure_filename

    filename = secure_filename(filename)
    filepath = os.path.join(config.UPLOAD_FOLDER, filename)
    file.seek(0)
    file.save(filepath)
    return jsonify({"url": f"/static/uploads/{filename}"})
