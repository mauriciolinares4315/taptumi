"""
Instancias de extensiones de Flask, creadas aqui sin `app` todavia
(patron application factory) y conectadas en app/__init__.py.
"""
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

cors = CORS()
limiter = Limiter(key_func=get_remote_address)
