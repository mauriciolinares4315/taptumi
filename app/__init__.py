"""
Application factory.

Uso:
    from app import create_app
    app = create_app()
"""
import os

from flask import Flask
from dotenv import load_dotenv

load_dotenv()

from app.config import config  # noqa: E402  (despues de load_dotenv a proposito)


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    config.validate()

    app.secret_key = config.SECRET_KEY
    app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

    # Cookies de sesion mas estrictas (la sesion solo guarda un flag booleano
    # de "puede crear perfiles", pero igual conviene protegerla bien).
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"

    _register_extensions(app)
    _register_blueprints(app)

    @app.context_processor
    def inject_globals():
        """Variables disponibles automaticamente en todos los templates."""
        return {"taptumi_landing_url": config.TAPTUMI_LANDING_URL}

    with app.app_context():
        from app.db import init_db

        init_db()

    return app


def _register_extensions(app):
    from app.extensions import cors, limiter

    # CORS solo se habilita para los origenes explicitamente permitidos.
    # Si CORS_ORIGINS esta vacio, no se agregan headers de CORS y el
    # navegador bloquea peticiones desde otros dominios (comportamiento
    # por defecto, mas seguro).
    if config.CORS_ORIGINS:
        cors.init_app(app, resources={r"/api/*": {"origins": config.CORS_ORIGINS}})

    limiter.init_app(app)


def _register_blueprints(app):
    from app.routes.public import public_bp
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
