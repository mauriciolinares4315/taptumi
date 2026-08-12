# 🎯 Guía: Empaquetar proyecto con venv

## ¿Qué es venv?

**venv** = **Virtual Environment** (Entorno Virtual)

Es una **carpeta aislada** donde instalas las librerías de Python.
Imagina que es una "caja aparte" dentro de tu computadora:

```
Tu computadora
├── Python 3.11 (global)
│   └── Flask 2.0 (instalado aquí)  ← NO tocar esto
│
└── nfc-profile-app/
    └── venv/                       ← TU CAJA AISLADA
        ├── Python 3.11 (copia)
        ├── Flask 3.0               ← Tu versión específica
        ├── Flask-CORS 4.0          ← Solo para este proyecto
        └── Werkzeug 3.0            ← Solo para este proyecto
```

**Ventajas:**
- ✅ Cada proyecto tiene sus propias versiones de librerías
- ✅ No contaminas el Python global de tu computadora
- ✅ Puedes compartir el proyecto completo (código + dependencias)
- ✅ Fácil de eliminar: borras la carpeta `venv` y listo

---

## 📋 Paso a paso

### 1. Abre terminal en la carpeta del proyecto

```bash
cd nfc-profile-app/
```

### 2. Crear el entorno virtual

```bash
python3 -m venv venv
```

Esto crea la carpeta `venv/` con Python y pip aislados.

### 3. Activar el entorno virtual

**En Linux/Mac:**
```bash
source venv/bin/activate
```

**En Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**En Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

Verás que el prompt cambia:
```
(venv) usuario@pc:~/nfc-profile-app$     ← El (venv) indica que está activo
```

### 4. Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Verás algo como:
```
Collecting flask==3.0.0
  Downloading flask-3.0.0-py3-none-any.whl
Collecting flask-cors==4.0.0
  Downloading flask_cors-4.0.0-py2.py3-none-any.whl
...
Successfully installed flask-3.0.0 flask-cors-4.0.0 werkzeug-3.0.1
```

### 5. Verificar que todo funciona

```bash
python -c "import flask; print(flask.__version__)"
# Debe imprimir: 3.0.0
```

### 6. Correr la app

```bash
python app.py
```

---

## 📁 Estructura final del proyecto

```
nfc-profile-app/
├── venv/                    ← ENTORNO VIRTUAL (no subir a GitHub)
│   ├── bin/                 ← Scripts y ejecutables
│   ├── lib/                 ← Librerías instaladas
│   └── pyvenv.cfg           ← Configuración del venv
│
├── app.py                   ← Tu código
├── profiles.db              ← Base de datos (no subir a GitHub)
├── requirements.txt         ← Lista de dependencias
├── setup.sh                 ← Script automático (opcional)
├── run.sh                   ← Script para correr (opcional)
├── README.md
├── templates/
│   ├── profile.html
│   ├── admin.html
│   └── 404.html
└── static/
    ├── css/
    │   ├── style.css
    │   └── admin.css
    ├── js/
    └── uploads/
```

---

## 🔄 Uso diario (después de configurar)

```bash
# 1. Ir al proyecto
cd nfc-profile-app/

# 2. Activar entorno
source venv/bin/activate        # Linux/Mac
# o
venv\Scripts\activate.bat     # Windows

# 3. Correr la app
python app.py

# 4. Cuando termines
deactivate
```

---

## ⚠️ IMPORTANTE: No subir venv a GitHub

Crea un archivo `.gitignore`:

```gitignore
# Python
venv/
__pycache__/
*.pyc
*.pyo

# Base de datos (para no subir datos reales)
profiles.db

# Subidas de usuarios
static/uploads/

# Variables de entorno
.env
```

---

## 🚀 Script automático (setup.sh)

Ya incluí `setup.sh` en el proyecto. Solo ejecuta:

```bash
bash setup.sh
```

Y hace todo automáticamente:
1. Crea venv
2. Lo activa
3. Instala dependencias
4. Verifica instalación
5. Crea script `run.sh`

Después solo usas:
```bash
bash run.sh
```

---

## ❌ Si algo falla

### Error: "python3 no encontrado"
```bash
# Prueba con python en lugar de python3
python -m venv venv
```

### Error: "pip no encontrado"
```bash
# Asegúrate de que pip esté instalado
python -m ensurepip --upgrade
```

### Error: "No se puede activar en PowerShell"
```powershell
# Ejecuta PowerShell como administrador y corre:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Luego intenta de nuevo: venv\Scripts\Activate.ps1
```

### Error: "ModuleNotFoundError: No module named 'flask'"
```bash
# Olvidaste activar el venv
source venv/bin/activate
# Luego: python app.py
```
