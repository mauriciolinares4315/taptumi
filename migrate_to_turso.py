#!/usr/bin/env python3
"""
Script para migrar la base de datos SQLite local a Turso.

Uso:
    python migrate_to_turso.py

Requisitos:
    - Tener TURSO_DATABASE_URL y TURSO_AUTH_TOKEN configurados
    - Tener libsql-client instalado: pip install libsql-client
"""

import sqlite3
import os
import sys

# Configuración de Turso
TURSO_DATABASE_URL = os.environ.get('TURSO_DATABASE_URL', '')
TURSO_AUTH_TOKEN = os.environ.get('TURSO_AUTH_TOKEN', '')

if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
    print("❌ Error: Debes configurar las variables de entorno:")
    print("   export TURSO_DATABASE_URL='libsql://tu-db.turso.io'")
    print("   export TURSO_AUTH_TOKEN='tu-token'")
    sys.exit(1)

try:
    import libsql_client
except ImportError:
    print("❌ Error: libsql-client no está instalado.")
    print("   pip install libsql-client")
    sys.exit(1)

print("🚀 Migrando base de datos SQLite a Turso...")
print(f"   Origen: profiles.db (local)")
print(f"   Destino: {TURSO_DATABASE_URL}")
print()

# Conectar a SQLite local
sqlite_conn = sqlite3.connect('profiles.db')
sqlite_conn.row_factory = sqlite3.Row

# Conectar a Turso
turso_conn = libsql_client.create_client_sync(
    url=TURSO_DATABASE_URL,
    auth_token=TURSO_AUTH_TOKEN
)

# Tablas a migrar
tables = ['profiles', 'social_links', 'stats', 'gallery']

for table in tables:
    print(f"📦 Migrando tabla: {table}")

    # Obtener datos de SQLite
    cursor = sqlite_conn.execute(f'SELECT * FROM {table}')
    rows = cursor.fetchall()

    if not rows:
        print(f"   ℹ️ Tabla vacía, saltando...")
        continue

    # Obtener nombres de columnas
    columns = [description[0] for description in cursor.description]
    placeholders = ', '.join(['?' for _ in columns])
    columns_str = ', '.join(columns)

    # Insertar en Turso
    count = 0
    for row in rows:
        values = tuple(row)
        turso_conn.execute(
            f'INSERT INTO {table} ({columns_str}) VALUES ({placeholders})',
            values
        )
        count += 1

    print(f"   ✅ {count} registros migrados")

sqlite_conn.close()
# turso_conn no tiene close() en algunas versiones

print()
print("🎉 ¡Migración completada!")
print("   Tu base de datos ahora vive en Turso.")
print("   Las imágenes deben subirse manualmente o re-subirse a Cloudinary.")
