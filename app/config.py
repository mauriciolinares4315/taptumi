"""
Configuracion de la aplicacion.

Todas las variables sensibles viven en el .env (nunca en este archivo
ni en el repositorio). Ver .env.example para la lista completa.
"""
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # Contrasena maestra para poder crear perfiles nuevos.
    MASTER_PASSWORD = os.environ.get("MASTER_PASSWORD")

    # Base de datos: si hay credenciales de Turso, se usa Turso (HTTP).
    # Si no, se cae a SQLite local (profiles.db) - util para desarrollo.
    TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL", "")
    TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")
    USE_TURSO = bool(TURSO_DATABASE_URL and TURSO_AUTH_TOKEN)
    SQLITE_PATH = os.environ.get("SQLITE_PATH", "profiles.db")

    # Cloudinary (almacenamiento de imagenes). Si no esta configurado,
    # las fotos se guardan localmente en static/uploads como fallback.
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "")

    UPLOAD_FOLDER = "static/uploads"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # Origenes permitidos para CORS. En produccion, define
    # CORS_ORIGINS="https://tudominio.com,https://otro.com" en el .env.
    # Vacio = no se habilita CORS de origen cruzado para la API.
    CORS_ORIGINS = [
        o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()
    ]

    # Limites de intentos (Flask-Limiter). Ajustables por env si hace falta.
    RATELIMIT_LOGIN = os.environ.get("RATELIMIT_LOGIN", "8 per minute")
    RATELIMIT_CREATE = os.environ.get("RATELIMIT_CREATE", "5 per minute")

    # Mensaje predeterminado que se precarga al escribir por WhatsApp desde
    # el botón del perfil público. Un solo lugar para editarlo en toda la app.
    WHATSAPP_DEFAULT_MESSAGE = os.environ.get(
        "WHATSAPP_DEFAULT_MESSAGE",
        "Hola, escaneé tu Taptumi Card y quiero ponerme en contacto contigo.",
    )
    # URL de la landing de marca (Taptumi), enlazada desde el footer de
    # todas las páginas. Placeholder hasta que definas el dominio real.
    TAPTUMI_LANDING_URL = os.environ.get("TAPTUMI_LANDING_URL", "/")

    def validate(self):
        """Falla rapido y claro si falta algo critico para arrancar."""
        missing = [
            name
            for name in ("SECRET_KEY", "MASTER_PASSWORD")
            if not getattr(self, name)
        ]
        if missing:
            raise ValueError(
                "Faltan variables de entorno obligatorias: "
                + ", ".join(missing)
                + ". Revisa tu archivo .env (usa .env.example como plantilla)."
            )


config = Config()
