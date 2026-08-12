# 🎯 NFC Digital Profile

Sistema de perfiles digitales activados por tarjetas NFC.

## 🚀 Inicio rapido

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar la aplicacion
```bash
python app.py
```

La app correra en: `http://localhost:5000`

### 3. Probar el perfil de ejemplo
- **Perfil publico:** http://localhost:5000/c/demo
- **Panel admin:** http://localhost:5000/admin/demo
- **Contrasena:** `admin123`

## 📁 Estructura del proyecto

```
nfc-profile-app/
├── app.py                  # Backend Flask (API + rutas)
├── profiles.db             # Base de datos SQLite (se crea al iniciar)
├── requirements.txt        # Dependencias
├── templates/
│   ├── profile.html        # Pagina publica (lo que ve quien escanea NFC)
│   ├── admin.html          # Panel de edicion
│   └── 404.html            # Pagina no encontrada
└── static/
    ├── css/
    │   ├── style.css       # Estilos del perfil publico
    │   └── admin.css       # Estilos del panel admin
    ├── js/                 # JavaScript (enlinea en los HTML por ahora)
    └── uploads/            # Imagenes subidas por usuarios
```

## 🔗 URLs importantes

| URL | Descripcion |
|-----|-------------|
| `/c/<slug>` | Perfil publico (lo que se ve al escanear NFC) |
| `/admin/<slug>` | Panel de edicion del perfil |
| `/api/profile/<slug>` | API JSON del perfil (GET) |
| `/api/profile/<slug>` | Actualizar perfil (POST + contrasena) |
| `/api/stats/<slug>` | Estadisticas de escaneos |
| `/api/upload` | Subir imagen |

## 🗄️ Base de datos (SQLite)

### Tablas:
- **profiles** - Datos del perfil
- **social_links** - Links a redes sociales
- **stats** - Registro de escaneos (fecha, IP, user-agent)
- **gallery** - Imagenes de la galeria

## 📝 Flujo de trabajo

1. **Tu (dev)** creas un perfil via API o directo en la DB
2. **Tu** escribes la URL en la tarjeta NFC (ej: `tusitio.com/c/maria-01`)
3. **El usuario** va a `/admin/maria-01` y edita su info con contrasena `admin123`
4. **Cualquiera** que escanee la NFC ve el perfil actualizado
5. **Cada escaneo** se guarda en `stats` para metricas

## 🛠️ Proximos pasos

- [ ] Subir a Render/Railway (backend) + Vercel (frontend)
- [ ] Agregar subida de fotos de perfil
- [ ] Agregar galeria de imagenes editable
- [ ] Sistema de plantillas/themes
- [ ] Generar QR como alternativa a NFC
- [ ] Exportar vCard (.vcf) al guardar contacto
