# 🎯 Taptumi — Perfiles digitales activados por NFC

Sistema de tarjetas digitales (tipo "linktree personal") activadas al escanear
un tag NFC. Backend Flask organizado por *blueprints*, base de datos
SQLite (local) o Turso (producción), imágenes en Cloudinary o disco local,
y una interfaz con estética de vidrio (glassmorfismo) oscuro.

## 🚀 Inicio rápido

### 1. Crear entorno y instalar dependencias
```bash
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
```
Edita `.env` y completa al menos `SECRET_KEY` y `MASTER_PASSWORD`
(puedes generar una `SECRET_KEY` con `python -c "import secrets; print(secrets.token_hex(32))"`).
Turso y Cloudinary son opcionales: si los dejas vacíos, la app usa SQLite
local y guarda las fotos en `static/uploads/`.

### 3. Ejecutar la aplicación
```bash
python wsgi.py
```
La app corre en `http://localhost:5000`. La primera vez, crea automáticamente
las tablas y un perfil de ejemplo (`demo` / contraseña `demo123`).

### 4. Probar el perfil de ejemplo
- **Perfil público:** http://localhost:5000/c/demo
- **Panel admin:** http://localhost:5000/admin/demo (contraseña `demo123`)
- **Crear perfil nuevo:** http://localhost:5000/create (pide la `MASTER_PASSWORD` del `.env`)

## 📁 Estructura del proyecto

```
nfc-profile-app/
├── wsgi.py                    # Punto de entrada (gunicorn wsgi:app)
├── app/
│   ├── __init__.py            # Application factory: crea y configura Flask
│   ├── config.py              # Lee y valida las variables de entorno
│   ├── db.py                  # Capa de datos (Turso HTTP / SQLite), agnóstica al backend
│   ├── security.py            # Hashing de contraseñas y utilidades de seguridad
│   ├── extensions.py          # CORS y rate limiting (Flask-Limiter)
│   ├── utils.py                # Validación de archivos, íconos sociales
│   └── routes/
│       ├── public.py          # GET /c/<slug> — página pública
│       ├── api.py             # /api/* — endpoints REST (JSON)
│       └── admin.py           # /admin/<slug>, /create — panel y creación
├── templates/
│   ├── profile.html           # Perfil público
│   ├── admin.html             # Panel de edición
│   ├── create_login.html      # Login con contraseña maestra
│   ├── create_profile.html    # Formulario de creación de perfiles
│   ├── gallery_carousel.html  # Parcial: carrusel de galería + lightbox
│   └── 404.html
├── static/
│   ├── css/
│   │   └── style.css          # Único CSS: sistema de diseño glassmorfismo
│   └── uploads/                # Fallback local de imágenes (si no hay Cloudinary)
├── .env.example                # Plantilla de variables de entorno (sin valores reales)
├── requirements.txt
├── Procfile / Dockerfile       # Despliegue (gunicorn wsgi:app)
└── migrate_to_turso.py
```

## 🎨 Sistema de diseño

Todo el frontend comparte un único archivo, `static/css/style.css`, con
variables CSS (`--glass-bg`, `--accent`, `--radius-card`, etc.) para que
cualquier página nueva herede automáticamente la misma estética: tarjetas
de vidrio (`.glass-card`), botones tipo píldora (`.btn`, `.btn-primary`,
`.btn-whatsapp`...), inputs con foco en azul, y el mismo fondo con
resplandor difuso en todas las pantallas.

Si agregas una página nueva, solo necesitas enlazar `style.css` y usar las
clases ya definidas — no crees un `<style>` nuevo por archivo.

## 🔐 Seguridad — qué cambió

| Antes | Ahora |
|---|---|
| Contraseñas en texto plano en la BD | Hash con `werkzeug.security` (migración automática de perfiles viejos) |
| Contraseña maestra en la URL (`/create?token=...`) | Sesión abierta vía `POST /create/access` |
| Sin límite de intentos | Rate limiting con Flask-Limiter en login, creación y subida de imágenes |
| CORS abierto a cualquier origen | Cerrado por defecto; se habilita solo si defines `CORS_ORIGINS` |
| `/api/upload` sin autenticación | Requiere sesión de creación o la contraseña del perfil |
| Links sociales renderizados con `innerHTML` (XSS) | Renderizados vía DOM (`createElement` + `.value`) |

## 🔗 URLs importantes

| Método | URL | Descripción |
|---|---|---|
| GET | `/c/<slug>` | Perfil público (lo que se ve al escanear el NFC) |
| GET | `/admin/<slug>` | Panel de edición del perfil |
| GET | `/create` | Formulario de creación (requiere sesión) |
| POST | `/create/access` | Valida la contraseña maestra y abre sesión |
| GET | `/api/profile/<slug>` | Obtener perfil (JSON) |
| POST | `/api/profile/<slug>` | Actualizar perfil (requiere contraseña) |
| POST | `/api/validate-password/<slug>` | Validar contraseña de un perfil |
| POST | `/api/create-profile` | Crear perfil nuevo (requiere sesión) |
| GET | `/api/stats/<slug>` | Estadísticas de escaneos |
| POST | `/api/upload` | Subir imagen (requiere autorización) |

## 🗄️ Base de datos

Tablas: `profiles`, `social_links`, `stats` (registro de escaneos), `gallery`.
Usa Turso (HTTP) si `TURSO_DATABASE_URL` y `TURSO_AUTH_TOKEN` están definidos
en el `.env`; si no, cae automáticamente a SQLite local (`profiles.db`).

## 📦 Despliegue

```bash
gunicorn wsgi:app
```
El `Procfile` y el `Dockerfile` ya apuntan a `wsgi:app`. En producción,
define `FLASK_ENV=production` para que las cookies de sesión se marquen
como `Secure` (requiere HTTPS).

## ⚠️ Antes de compartir este proyecto

Nunca comprimas la carpeta completa a mano para compartirla — arrastraría
tu `.env` real, `profiles.db` y las fotos subidas. Usa:
```bash
git archive -o proyecto.zip HEAD
```
Esto respeta el `.gitignore` y solo empaqueta lo que está versionado.

## 🛠️ Próximos pasos sugeridos

- [ ] Mover `SOCIAL_ICONS` y otras constantes a un archivo de configuración si la lista crece
- [ ] Agregar tests automatizados (ya hay una base con `app.test_client()`)
- [ ] Sistema de temas/colores por perfil (la columna `theme_color` ya existe pero no se usa en la UI)
- [ ] Generar QR como alternativa al tag NFC
