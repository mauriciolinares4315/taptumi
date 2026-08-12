# 🗄️ Guía Rápida: Turso para tu proyecto NFC

## ¿Qué es Turso?

Turso es **SQLite en la nube**. Es la misma base de datos que ya usas, pero alojada
en servidores distribuidos globalmente. Nada se pierde al reiniciar el servidor.

---

## 🚀 Paso 1: Crear cuenta y base de datos

1. Ve a [turso.tech](https://turso.tech)
2. Clic en **"Get Started"** → Regístrate (puedes usar GitHub)
3. Instala la CLI de Turso:

```bash
# Mac/Linux
curl -sSfL https://get.tur.so/install.sh | bash

# Windows (PowerShell como admin)
irm https://get.tur.so/install.ps1 | iex
```

4. Login:
```bash
turso auth login
```

5. Crear base de datos:
```bash
turso db create nfc-profiles
```

6. Obtener URL y token:
```bash
# URL de la base de datos
turso db show nfc-profiles
# Ejemplo: libsql://nfc-profiles-TUUSUARIO.turso.io

# Token de autenticación
turso db tokens create nfc-profiles
# Copia el token que te devuelve
```

---

## 🔧 Paso 2: Configurar variables de entorno

### Desarrollo local (archivo .env):

Crea un archivo `.env` en la carpeta del proyecto:

```env
TURSO_DATABASE_URL=libsql://nfc-profiles-TUUSUARIO.turso.io
TURSO_AUTH_TOKEN=tu-token-aqui
```

### En Render (producción):

Ve al Dashboard de tu Web Service → **Environment** → Agrega:

| Variable | Valor |
|----------|-------|
| `TURSO_DATABASE_URL` | `libsql://nfc-profiles-TUUSUARIO.turso.io` |
| `TURSO_AUTH_TOKEN` | `tu-token-aqui` |

---

## 📦 Paso 3: Migrar datos de SQLite a Turso

### Opción A: Script automático (recomendado)

```bash
# 1. Configurar variables
export TURSO_DATABASE_URL="libsql://nfc-profiles-TUUSUARIO.turso.io"
export TURSO_AUTH_TOKEN="tu-token-aqui"

# 2. Instalar libsql-client
pip install libsql-client

# 3. Correr migración
python migrate_to_turso.py
```

### Opción B: Manual con turso CLI

```bash
# Crear tablas en Turso
turso db shell nfc-profiles

# Dentro del shell, pega las sentencias CREATE TABLE de app.py
# Luego sal con .quit

# Insertar datos manualmente o usar el script
```

---

## ✅ Paso 4: Verificar que funciona

```bash
# Activar entorno
source venv/bin/activate

# Configurar variables (o tener .env)
export TURSO_DATABASE_URL="..."
export TURSO_AUTH_TOKEN="..."

# Correr la app
python app.py
```

Abre `http://localhost:5000/c/demo` — debería funcionar igual que antes,
pero ahora los datos vienen de Turso.

---

## 💰 Precios de Turso

| Plan | Precio | Qué incluye |
|------|--------|-------------|
| **Starter (Free)** | $0 | 5GB, 500M reads/mes, 1 base de datos |
| **Developer** | $4.99/mes | 9GB, 2.5B reads/mes, DBs ilimitadas |
| **Pro** | $29/mes | 100GB, reads ilimitadas, soporte prioritario |

Para tu proyecto, el plan **Starter (gratis)** es suficiente para empezar.

---

## 🔄 Flujo completo

```
1. Creas perfil en tu app
        ↓
2. Flask guarda en Turso (SQLite en la nube)
        ↓
3. Render reinicia (sleep/wake)
        ↓
4. Flask se reconecta a Turso
        ↓
5. Todos los datos siguen ahí ✅
```

---

## 🆘 Solución de problemas

### "libsql_client not found"
```bash
pip install libsql-client
```

### "Authentication failed"
- Verifica que `TURSO_AUTH_TOKEN` sea correcto
- Genera un nuevo token: `turso db tokens create nfc-profiles`

### "Database not found"
- Verifica la URL: `turso db show nfc-profiles`
- Asegúrate de incluir `libsql://` al inicio

### Datos no aparecen después de migrar
- Verifica que las tablas existan en Turso: `turso db shell nfc-profiles`
- Corre `.tables` dentro del shell

---

## 📚 Recursos

- [Turso Docs](https://docs.turso.tech)
- [Turso Python Client](https://docs.turso.tech/sdk/python)
- [Turso CLI Reference](https://docs.turso.tech/reference/turso-cli)
