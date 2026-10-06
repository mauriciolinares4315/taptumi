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
# ---------- Bloqueo por intentos fallidos ----------
from datetime import datetime, timedelta, timezone

MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def is_locked(locked_until_iso) -> bool:
    """¿Sigue vigente el bloqueo?"""
    if not locked_until_iso:
        return False
    try:
        lock_dt = datetime.fromisoformat(locked_until_iso)
        # Normalizar por si el string no tiene tzinfo
        if lock_dt.tzinfo is None:
            lock_dt = lock_dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return False
    return now_utc() < lock_dt


def remaining_lock_minutes(locked_until_iso) -> int:
    """Cuántos minutos faltan para que expire el bloqueo (0 si ya expiró)."""
    if not locked_until_iso:
        return 0
    try:
        lock_dt = datetime.fromisoformat(locked_until_iso)
        if lock_dt.tzinfo is None:
            lock_dt = lock_dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return 0
    delta = lock_dt - now_utc()
    if delta.total_seconds() <= 0:
        return 0
    return max(1, int(delta.total_seconds() // 60) + 1)


def next_lock_timestamp() -> str:
    """ISO timestamp de cuándo expira un nuevo bloqueo."""
    return (now_utc() + timedelta(minutes=LOCK_DURATION_MINUTES)).isoformat()