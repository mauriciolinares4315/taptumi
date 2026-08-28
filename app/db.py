"""
Capa de acceso a datos.

Expone get_db() e init_db(), que funcionan igual sin importar si el
backend real es Turso (HTTP) o SQLite local. El resto de la app nunca
deberia importar sqlite3/requests directamente - todo pasa por aqui.
"""
import base64
import sqlite3

import requests

from app.config import config

SOCIAL_ICONS = {
    "instagram": "fab fa-instagram",
    "facebook": "fab fa-facebook-f",
    "twitter": "fab fa-x-twitter",
    "x": "fab fa-x-twitter",
    "linkedin": "fab fa-linkedin-in",
    "tiktok": "fab fa-tiktok",
    "youtube": "fab fa-youtube",
    "whatsapp": "fab fa-whatsapp",
    "spotify": "fab fa-spotify",
    "github": "fab fa-github",
    "behance": "fab fa-behance",
    "dribbble": "fab fa-dribbble",
    "pinterest": "fab fa-pinterest",
    "telegram": "fab fa-telegram",
    "snapchat": "fab fa-snapchat",
    "globe": "fas fa-globe",
    "link": "fas fa-link",
    "envelope": "fas fa-envelope",
    "phone": "fas fa-phone",
    "default": "fas fa-link",
}


def extract_turso_value(cell):
    """Extrae el valor Python nativo de una celda tipada de Turso."""
    if cell is None:
        return None
    if isinstance(cell, dict):
        t = cell.get("type")
        v = cell.get("value")
        if t == "null":
            return None
        elif t == "integer":
            return int(v)
        elif t == "float":
            return float(v)
        elif t == "blob":
            return base64.b64decode(v)
        else:  # text
            return v
    return cell


class TursoRow:
    """Emula sqlite3.Row para que funcione dict(row) y row[0]/row['col']."""

    def __init__(self, columns, values):
        self._columns = columns
        self._values = [extract_turso_value(v) for v in values]

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        if key in self._columns:
            return self._values[self._columns.index(key)]
        raise KeyError(key)

    def __iter__(self):
        return iter(self._columns)

    def keys(self):
        return self._columns


class FakeCursor:
    """Cursor falso para Turso HTTP (para que el resto del codigo sea agnostico)."""

    def __init__(self, rows=None, rowcount=0, lastrowid=0):
        self.rows = rows or []
        self.rowcount = rowcount
        self.lastrowid = lastrowid


def to_turso_args(values):
    """Convierte valores Python al formato tipado que espera la API v2 de Turso."""
    args = []
    for v in values:
        if v is None:
            args.append({"type": "null"})
        elif isinstance(v, bool):
            args.append({"type": "integer", "value": str(int(v))})
        elif isinstance(v, int):
            args.append({"type": "integer", "value": str(v)})
        elif isinstance(v, float):
            args.append({"type": "float", "value": str(v)})
        elif isinstance(v, bytes):
            args.append({"type": "blob", "base64": base64.b64encode(v).decode()})
        else:
            args.append({"type": "text", "value": str(v)})
    return args


class DBConnection:
    """Wrapper que maneja tanto Turso (HTTP) como SQLite de forma transparente."""

    def __init__(self, conn):
        self.conn = conn
        self.is_turso = config.USE_TURSO and isinstance(conn, str)

    def execute(self, query, params=()):
        if self.is_turso:
            url = f"{self.conn}/v2/pipeline"
            headers = {
                "Authorization": f"Bearer {config.TURSO_AUTH_TOKEN}",
                "Content-Type": "application/json",
            }
            stmt = {"sql": query}
            if params:
                stmt["args"] = to_turso_args(list(params))

            payload = {
                "requests": [
                    {"type": "execute", "stmt": stmt},
                    {"type": "close"},
                ]
            }
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code >= 400:
                raise RuntimeError(f"Turso error {r.status_code}: {r.text[:300]}")
            r.raise_for_status()
            data = r.json()

            result = data["results"][0]["response"]["result"]
            cols = [c["name"] for c in result.get("cols", [])]
            rows = [TursoRow(cols, row) for row in result.get("rows", [])]
            rowcount = result.get("affected_row_count", 0)
            lastrowid = result.get("last_insert_rowid", 0)

            return FakeCursor(rows=rows, rowcount=rowcount, lastrowid=lastrowid)
        else:
            return self.conn.execute(query, params)

    def fetchone(self, cursor):
        if self.is_turso:
            rows = cursor.rows if hasattr(cursor, "rows") else []
            return rows[0] if rows else None
        return cursor.fetchone()

    def fetchall(self, cursor):
        if self.is_turso:
            return cursor.rows if hasattr(cursor, "rows") else []
        return cursor.fetchall()

    def commit(self):
        if not self.is_turso:
            self.conn.commit()

    def close(self):
        if not self.is_turso:
            self.conn.close()


def get_db():
    """Obtiene una conexion (Turso HTTP o SQLite local, segun configuracion)."""
    if config.USE_TURSO:
        return DBConnection(config.TURSO_DATABASE_URL.replace("libsql://", "https://"))

    conn = sqlite3.connect(config.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return DBConnection(conn)


def init_db():
    """Crea las tablas si no existen, e inserta un perfil de ejemplo la primera vez."""
    db = get_db()

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL DEFAULT '',
            role TEXT DEFAULT '',
            company TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            whatsapp TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            photo_url TEXT DEFAULT '',
            password TEXT NOT NULL,
            theme_color TEXT DEFAULT '#1a1a2e',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS social_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            url TEXT NOT NULL,
            label TEXT DEFAULT '',
            icon TEXT DEFAULT 'link',
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT DEFAULT '',
            user_agent TEXT DEFAULT ''
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS gallery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            image_url TEXT NOT NULL,
            caption TEXT DEFAULT '',
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
        )
        """
    )

    # Perfil de ejemplo, solo si la tabla esta vacia de verdad (primera vez).
    from app.security import hash_password

    existing = db.fetchone(db.execute("SELECT id FROM profiles WHERE slug = ?", ("demo",)))
    if not existing:
        db.execute(
            """
            INSERT INTO profiles (slug, name, role, company, bio, whatsapp, email, phone, password, theme_color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "demo",
                "Maria Gonzalez",
                "Disenadora Grafica",
                "Estudio Creativo MGX",
                "Creo identidades visuales que cuentan historias. Especializada en branding, packaging y diseno digital.",
                "573001234567",
                "maria@mgxstudio.com",
                "+57 300 123 4567",
                hash_password("demo123"),
                "#1a1a2e",
            ),
        )
        profile_id = db.fetchone(db.execute("SELECT id FROM profiles WHERE slug = ?", ("demo",)))[0]

        links = [
            ("Instagram", "https://instagram.com/mgxstudio", "@mgxstudio", "instagram", 1),
            ("Behance", "https://behance.net/mgxstudio", "Portafolio", "behance", 2),
            ("Sitio Web", "https://mgxstudio.com", "mgxstudio.com", "globe", 3),
        ]
        for platform, url, label, icon, order in links:
            db.execute(
                """
                INSERT INTO social_links (profile_id, platform, url, label, icon, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (profile_id, platform, url, label, icon, order),
            )

    db.commit()
    db.close()
