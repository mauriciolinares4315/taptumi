from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
import sqlite3
import os
import uuid
import re
from datetime import datetime
from werkzeug.utils import secure_filename

# Cloudinary para almacenamiento de imagenes en la nube
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

# Configuracion de Cloudinary (usa variables de entorno en produccion)
if CLOUDINARY_AVAILABLE:
    cloudinary.config(
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
        api_key=os.environ.get('CLOUDINARY_API_KEY', ''),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET', ''),
        secure=True
    )

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'tu-clave-secreta-cambia-esto')
CORS(app)

# Configuracion
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Contrasena maestra para crear perfiles (cambiala en produccion)
MASTER_PASSWORD = os.environ.get('MASTER_PASSWORD', 'nfc-admin-2024')

# ============================================================
# BASE DE DATOS (Turso con fallback a SQLite local)
# ============================================================

TURSO_DATABASE_URL = os.environ.get('TURSO_DATABASE_URL', '')
TURSO_AUTH_TOKEN = os.environ.get('TURSO_AUTH_TOKEN', '')
USE_TURSO = bool(TURSO_DATABASE_URL and TURSO_AUTH_TOKEN)

class DBConnection:
    """Wrapper que maneja tanto Turso como SQLite de forma transparente"""
    def __init__(self, conn):
        self.conn = conn
        self.is_turso = USE_TURSO and not isinstance(conn, sqlite3.Connection)

    def execute(self, query, params=()):
        """Ejecuta una query y devuelve un cursor/resultado"""
        if self.is_turso:
            return self.conn.execute(query, params)
        else:
            return self.conn.execute(query, params)

    def fetchone(self, cursor):
        """Obtiene una fila"""
        if self.is_turso:
            rows = cursor.rows if hasattr(cursor, 'rows') else []
            return rows[0] if rows else None
        else:
            return cursor.fetchone()

    def fetchall(self, cursor):
        """Obtiene todas las filas"""
        if self.is_turso:
            return cursor.rows if hasattr(cursor, 'rows') else []
        else:
            return cursor.fetchall()

    def commit(self):
        """Commit de transacciones (solo SQLite)"""
        if not self.is_turso:
            self.conn.commit()

    def close(self):
        """Cierra la conexion"""
        self.conn.close()

def get_db():
    """Obtiene conexion a Turso o SQLite local"""
    if USE_TURSO:
        try:
            import libsql_client
            conn = libsql_client.create_client_sync(
                url=TURSO_DATABASE_URL,
                auth_token=TURSO_AUTH_TOKEN
            )
            return DBConnection(conn)
        except Exception as e:
            print(f"⚠️ Error conectando a Turso: {e}")
            print("🔄 Fallback a SQLite local")

    # Fallback: SQLite local
    conn = sqlite3.connect('profiles.db')
    conn.row_factory = sqlite3.Row
    return DBConnection(conn)

def init_db():
    """Crea las tablas si no existen"""
    db = get_db()

    # Tabla de perfiles
    db.execute("""
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
            password TEXT DEFAULT 'admin123',
            theme_color TEXT DEFAULT '#1a1a2e',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabla de links sociales
    db.execute("""
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
    """)

    # Tabla de estadisticas (escaneos)
    db.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT DEFAULT '',
            user_agent TEXT DEFAULT ''
        )
    """)

    # Tabla de galeria
    db.execute("""
        CREATE TABLE IF NOT EXISTS gallery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            image_url TEXT NOT NULL,
            caption TEXT DEFAULT '',
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
        )
    """)

    # Insertar perfil de ejemplo si no existe
    existing = db.fetchone(db.execute('SELECT id FROM profiles WHERE slug = ?', ('demo',)))
    if not existing:
        db.execute("""
            INSERT INTO profiles (slug, name, role, company, bio, whatsapp, email, phone, theme_color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'demo',
            'Maria Gonzalez',
            'Disenadora Grafica',
            'Estudio Creativo MGX',
            'Creo identidades visuales que cuentan historias. Especializada en branding, packaging y diseno digital.',
            '573001234567',
            'maria@mgxstudio.com',
            '+57 300 123 4567',
            '#1a1a2e'
        ))
        profile_id = db.fetchone(db.execute('SELECT id FROM profiles WHERE slug = ?', ('demo',)))[0]

        # Links de ejemplo
        links = [
            ('Instagram', 'https://instagram.com/mgxstudio', '@mgxstudio', 'instagram', 1),
            ('Behance', 'https://behance.net/mgxstudio', 'Portafolio', 'behance', 2),
            ('Sitio Web', 'https://mgxstudio.com', 'mgxstudio.com', 'globe', 3),
        ]
        for platform, url, label, icon, order in links:
            db.execute("""
                INSERT INTO social_links (profile_id, platform, url, label, icon, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (profile_id, platform, url, label, icon, order))

    db.commit()
    db.close()
    print("✅ Base de datos inicializada")

# ============================================================
# RUTAS PUBLICAS (lo que ve quien escanea la NFC)
# ============================================================

@app.route('/c/<slug>')
def public_profile(slug):
    """Pagina publica del perfil - lo que se ve al escanear la NFC"""
    db = get_db()
    profile = db.fetchone(db.execute('SELECT * FROM profiles WHERE slug = ?', (slug,)))

    if not profile:
        db.close()
        return render_template('404.html'), 404

    # Registrar escaneo
    db.execute("""
        INSERT INTO stats (slug, ip_address, user_agent)
        VALUES (?, ?, ?)
    """, (slug, request.remote_addr, str(request.user_agent)[:200]))
    db.commit()

    # Obtener links sociales
    links = db.fetchall(db.execute("""
        SELECT * FROM social_links 
        WHERE profile_id = ? 
        ORDER BY sort_order
    """, (profile[0],)))

    # Obtener galeria
    gallery = db.fetchall(db.execute("""
        SELECT * FROM gallery 
        WHERE profile_id = ? 
        ORDER BY sort_order
    """, (profile[0],)))

    # Contar escaneos totales
    total_scans = db.fetchone(db.execute("""
        SELECT COUNT(*) as count FROM stats WHERE slug = ?
    """, (slug,)))[0]

    db.close()

    return render_template('profile.html', 
                         profile=profile, 
                         links=links, 
                         gallery=gallery,
                         total_scans=total_scans)

# ============================================================
# API REST
# ============================================================

@app.route('/api/profile/<slug>')
def api_get_profile(slug):
    """API: Obtener perfil como JSON"""
    db = get_db()
    profile = db.fetchone(db.execute('SELECT * FROM profiles WHERE slug = ?', (slug,)))

    if not profile:
        db.close()
        return jsonify({'error': 'Perfil no encontrado'}), 404

    links = db.fetchall(db.execute("""
        SELECT platform, url, label, icon FROM social_links 
        WHERE profile_id = ? ORDER BY sort_order
    """, (profile[0],)))

    gallery = db.fetchall(db.execute("""
        SELECT image_url, caption FROM gallery 
        WHERE profile_id = ? ORDER BY sort_order
    """, (profile[0],)))

    db.close()

    return jsonify({
        'slug': profile[1],
        'name': profile[2],
        'role': profile[3],
        'company': profile[4],
        'bio': profile[5],
        'whatsapp': profile[6],
        'email': profile[7],
        'phone': profile[8],
        'photo_url': profile[9],
        'theme_color': profile[11],
        'links': [dict(link) for link in links],
        'gallery': [dict(img) for img in gallery]
    })

@app.route('/api/validate-password/<slug>', methods=['POST'])
def api_validate_password(slug):
    """API: Validar contraseña de un perfil (solo para login)"""
    data = request.get_json()
    password = data.get('password', '')

    db = get_db()
    profile = db.fetchone(db.execute('SELECT password FROM profiles WHERE slug = ?', (slug,)))
    db.close()

    if not profile:
        return jsonify({'error': 'Perfil no encontrado'}), 404

    if password == profile[0]:
        return jsonify({'valid': True}), 200
    else:
        return jsonify({'valid': False, 'error': 'Contraseña incorrecta'}), 401

@app.route('/api/profile/<slug>', methods=['POST'])
def api_update_profile(slug):
    """API: Actualizar perfil (requiere contrasena)"""
    data = request.get_json()

    db = get_db()
    profile = db.fetchone(db.execute('SELECT * FROM profiles WHERE slug = ?', (slug,)))

    if not profile:
        db.close()
        return jsonify({'error': 'Perfil no encontrado'}), 404

    # Verificar contrasena
    if data.get('password') != profile[10]:
        db.close()
        return jsonify({'error': 'Contrasena incorrecta'}), 401

    # Actualizar campos basicos
    db.execute("""
        UPDATE profiles SET
            name = ?, role = ?, company = ?, bio = ?,
            whatsapp = ?, email = ?, phone = ?, photo_url = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE slug = ?
    """, (
        data.get('name', profile[2]),
        data.get('role', profile[3]),
        data.get('company', profile[4]),
        data.get('bio', profile[5]),
        data.get('whatsapp', profile[6]),
        data.get('email', profile[7]),
        data.get('phone', profile[8]),
        data.get('photo_url', profile[9]),
        slug
    ))

    # Actualizar links sociales (eliminar y recrear)
    if 'links' in data:
        db.execute('DELETE FROM social_links WHERE profile_id = ?', (profile[0],))
        for i, link in enumerate(data['links']):
            db.execute("""
                INSERT INTO social_links (profile_id, platform, url, label, icon, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (profile[0], link['platform'], link['url'], link['label'], link.get('icon', 'link'), i))

    # Actualizar galeria (eliminar y recrear)
    if 'gallery' in data:
        db.execute('DELETE FROM gallery WHERE profile_id = ?', (profile[0],))
        for i, img in enumerate(data['gallery'][:4]):
            db.execute("""
                INSERT INTO gallery (profile_id, image_url, caption, sort_order)
                VALUES (?, ?, ?, ?)
            """, (profile[0], img['image_url'], img.get('caption', ''), i))

    db.commit()
    db.close()

    return jsonify({'success': True, 'message': 'Perfil actualizado'})

@app.route('/api/stats/<slug>')
def api_get_stats(slug):
    """API: Obtener estadisticas de escaneos"""
    db = get_db()

    total = db.fetchone(db.execute('SELECT COUNT(*) as count FROM stats WHERE slug = ?', (slug,)))[0]

    # Escaneos por dia (ultimos 30 dias)
    daily = db.fetchall(db.execute("""
        SELECT DATE(scanned_at) as date, COUNT(*) as count 
        FROM stats 
        WHERE slug = ? AND scanned_at >= date('now', '-30 days')
        GROUP BY DATE(scanned_at)
        ORDER BY date
    """, (slug,)))

    db.close()

    return jsonify({
        'total_scans': total,
        'daily_scans': [dict(row) for row in daily]
    })

# ============================================================
# CREACION DINAMICA DE PERFILES
# ============================================================

@app.route('/create')
def create_profile_page():
    """Pagina para crear un nuevo perfil (requiere contrasena maestra)"""
    token = request.args.get('token', '')
    if token != MASTER_PASSWORD:
        return render_template('create_login.html')
    return render_template('create_profile.html')

@app.route('/api/create-profile', methods=['POST'])
def api_create_profile():
    """API: Crear un nuevo perfil dinamicamente (requiere contrasena maestra)"""
    data = request.get_json()

    # Verificar contrasena maestra
    master_pass = data.get('master_password', '')
    if master_pass != MASTER_PASSWORD:
        return jsonify({'error': 'Contrasena maestra incorrecta'}), 401

    # Validar datos minimos
    slug = data.get('slug', '').strip().lower()
    name = data.get('name', '').strip()
    password = data.get('password', '')

    if not slug:
        return jsonify({'error': 'El slug es obligatorio'}), 400
    if not name:
        return jsonify({'error': 'El nombre es obligatorio'}), 400
    if len(password) < 6:
        return jsonify({'error': 'La contrasena debe tener al menos 6 caracteres'}), 400

    # Limpiar slug
    slug = re.sub(r'[^a-z0-9-]', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')

    if not slug:
        return jsonify({'error': 'Slug invalido'}), 400

    db = get_db()

    # Verificar si el slug ya existe
    existing = db.fetchone(db.execute('SELECT id FROM profiles WHERE slug = ?', (slug,)))
    if existing:
        db.close()
        return jsonify({'error': f'El slug "{slug}" ya esta en uso. Elige otro.'}), 400

    # Crear el perfil
    try:
        db.execute("""
            INSERT INTO profiles (slug, name, role, company, bio, whatsapp, email, phone, photo_url, password, theme_color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            slug,
            name,
            data.get('role', ''),
            data.get('company', ''),
            '',
            data.get('whatsapp', ''),
            data.get('email', ''),
            data.get('phone', ''),
            data.get('photo_url', ''),
            password,
            '#1a1a2e'
        ))
        db.commit()
        db.close()

        return jsonify({
            'success': True,
            'slug': slug,
            'public_url': f'/c/{slug}',
            'admin_url': f'/admin/{slug}'
        })
    except Exception as e:
        db.close()
        return jsonify({'error': f'Error al crear perfil: {str(e)}'}), 500

# ============================================================
# RUTAS DE ADMIN
# ============================================================

@app.route('/admin/<slug>')
def admin_panel(slug):
    """Panel de administracion"""
    return render_template('admin.html', slug=slug)

# ============================================================
# UTILIDADES
# ============================================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Subir imagen a Cloudinary (o localmente como fallback)"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No filename'}), 400

    # Intentar Cloudinary primero si esta disponible y configurado
    if CLOUDINARY_AVAILABLE and os.environ.get('CLOUDINARY_CLOUD_NAME'):
        try:
            result = cloudinary.uploader.upload(
                file,
                folder="nfc-profiles",
                transformation=[
                    {"width": 1200, "height": 1200, "crop": "limit"},
                    {"quality": "auto", "fetch_format": "auto"}
                ]
            )
            return jsonify({
                'url': result['secure_url'],
                'public_id': result['public_id']
            })
        except Exception as e:
            pass

    # Fallback: guardar localmente
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.seek(0)
        file.save(filepath)
        return jsonify({'url': f'/static/uploads/{filename}'})

    return jsonify({'error': 'Invalid file or upload failed'}), 400

# ============================================================
# INICIO
# ============================================================

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
