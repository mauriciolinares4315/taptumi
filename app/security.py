"""
Utilidades de seguridad: hashing de contrasenas y limpieza de slugs.
"""
import re
import hmac

from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(plain_password: str) -> str:
    """Genera un hash seguro (pbkdf2) para guardar en la base de datos."""
    return generate_password_hash(plain_password)


def verify_password(plain_password: str, stored_value: str) -> bool:
    """
    Verifica una contrasena contra lo guardado en la BD.

    Soporta perfiles viejos que aun tengan la contrasena en texto plano
    (creados antes de este cambio) para no romperles el acceso: si el
    valor guardado no tiene forma de hash, compara en texto plano y
    devuelve un flag para que el caller pueda migrarlo sobre la marcha.
    """
    if not stored_value:
        return False
    if stored_value.startswith(("pbkdf2:", "scrypt:")):
        return check_password_hash(stored_value, plain_password)
    # Valor legado en texto plano: comparacion segura contra timing attacks.
    return hmac.compare_digest(plain_password, stored_value)


def is_legacy_plaintext(stored_value: str) -> bool:
    return bool(stored_value) and not stored_value.startswith(("pbkdf2:", "scrypt:"))


def verify_master_password(candidate: str, expected: str) -> bool:
    """Comparacion segura (constante en tiempo) para la contrasena maestra."""
    if not candidate or not expected:
        return False
    return hmac.compare_digest(candidate, expected)


def clean_slug(raw_slug: str) -> str:
    """Normaliza un slug: minusculas, solo [a-z0-9-], sin guiones repetidos/extremos."""
    slug = raw_slug.strip().lower()
    slug = re.sub(r"[^a-z0-9-]", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug
