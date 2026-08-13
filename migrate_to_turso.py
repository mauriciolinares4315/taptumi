#!/usr/bin/env python3
"""
Migrar SQLite local → Turso (vía HTTP API v2)
"""

import sqlite3
import os
import sys
import requests
import base64

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TURSO_URL = os.environ.get('TURSO_DATABASE_URL', '').replace("libsql://", "https://")
TURSO_TOKEN = os.environ.get('TURSO_AUTH_TOKEN', '')

if not TURSO_URL or not TURSO_TOKEN:
    print("❌ Configura TURSO_DATABASE_URL y TURSO_AUTH_TOKEN en tu .env")
    sys.exit(1)


def to_turso_args(values):
    """Convierte valores Python al formato tipado de Turso v2 API"""
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


def turso_batch(statements):
    """Ejecuta múltiples statements en Turso vía HTTP"""
    url = f"{TURSO_URL}/v2/pipeline"
    headers = {
        "Authorization": f"Bearer {TURSO_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Agregar close al final de cada batch
    requests_list = statements.copy()
    requests_list.append({"type": "close"})
    
    payload = {"requests": requests_list}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    
    if r.status_code >= 400:
        print(f"❌ Turso error {r.status_code}: {r.text[:500]}")
    
    r.raise_for_status()
    return r.json()


print("🚀 Migrando SQLite → Turso")
print(f"   Origen: profiles.db")
print(f"   Destino: {TURSO_URL.replace('https://', 'libsql://')}")
print()

sqlite_conn = sqlite3.connect('profiles.db')
sqlite_conn.row_factory = sqlite3.Row

tables = ['profiles', 'social_links', 'stats', 'gallery']

for table in tables:
    print(f"📦 Migrando tabla: {table}")

    cursor = sqlite_conn.execute(f'SELECT * FROM {table}')
    rows = cursor.fetchall()

    if not rows:
        print(f"   ℹ️ Vacía, saltando...")
        continue

    columns = [d[0] for d in cursor.description]
    placeholders = ', '.join(['?' for _ in columns])
    cols = ', '.join(columns)

    BATCH_SIZE = 50
    batch = []
    count = 0

    for row in rows:
        # Construir stmt sin args si no hay valores (aunque aquí siempre hay)
        stmt = {
            "sql": f'INSERT INTO {table} ({cols}) VALUES ({placeholders})',
            "args": to_turso_args(list(row))
        }
        batch.append({"type": "execute", "stmt": stmt})

        if len(batch) >= BATCH_SIZE:
            turso_batch(batch)
            count += len(batch)
            batch = []
            print(f"   ⏳ {count} registros...", end="\r")

    if batch:
        turso_batch(batch)
        count += len(batch)

    print(f"   ✅ {count} registros migrados    ")

sqlite_conn.close()
print()
print("🎉 ¡Migración completada!")