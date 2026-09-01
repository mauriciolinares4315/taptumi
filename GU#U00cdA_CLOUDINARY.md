# ☁️ Guía: Migrar imágenes a Cloudinary (Almacenamiento en la nube)

## ¿Por qué Cloudinary?

| Problema con static/uploads/ | Solución Cloudinary |
|------------------------------|---------------------|
| Se borran al reiniciar servidor en Render | **Persisten para siempre** en la nube |
| Ocupan espacio en tu servidor | **No ocupan espacio** en tu app |
| Carga lenta desde tu servidor | **CDN global** = carga ultra rápida |
| Sin optimización automática | **Redimensiona, comprime, convierte** automático |
| Backup manual de archivos | **Backup automático** en la nube |

---

## 🚀 PASO 1: Crear cuenta en Cloudinary

1. Ve a [cloudinary.com](https://cloudinary.com)
2. Clic en **"Sign up for free"**
3. Regístrate con email o cuenta Google
4. Verifica tu email

---

## 🚀 PASO 2: Obtener credenciales

En tu dashboard de Cloudinary:

1. Ve a **"Settings"** (rueda dentada arriba a la derecha)
2. Ve a la pestaña **"API Keys"**
3. Verás estos datos:

```
Cloud Name:   tu-cloud-name
API Key:      123456789012345
API Secret:   abcdefgh1234567890abcdef
```

4. **Copia estos 3 valores** los necesitarás en tu app

---

## 🚀 PASO 3: Instalar Cloudinary en tu proyecto

```bash
pip install cloudinary
```

Agregar a `requirements.txt`:
```
cloudinary==1.38.0
```

---

## 🚀 PASO 4: Configurar Cloudinary en app.py

Agrega esto al inicio de `app.py` (después de las importaciones):

```python
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Configuración de Cloudinary
# En desarrollo local, usa estas credenciales directas
# En producción (Render), usa variables de entorno
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'tu-cloud-name'),
    api_key=os.environ.get('CLOUDINARY_API_KEY', 'tu-api-key'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET', 'tu-api-secret'),
    secure=True
)
```

---

## 🚀 PASO 5: Actualizar la ruta de upload

Reemplaza la función `upload_image` actual por esta:

```python
@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Subir imagen a Cloudinary"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No filename'}), 400

    try:
        # Subir a Cloudinary
        result = cloudinary.uploader.upload(
            file,
            folder="nfc-profiles",  # Carpeta organizadora
            transformation=[
                {"width": 800, "height": 800, "crop": "limit"},  # Limitar tamaño
                {"quality": "auto", "fetch_format": "auto"}  # Optimizar automático
            ]
        )

        # Devolver la URL segura
        return jsonify({
            'url': result['secure_url'],
            'public_id': result['public_id']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## 🚀 PASO 6: Configurar variables de entorno en Render

### En tu computadora (desarrollo local):

Crea un archivo `.env` en la raíz del proyecto:

```
CLOUDINARY_CLOUD_NAME=tu-cloud-name
CLOUDINARY_API_KEY=tu-api-key
CLOUDINARY_API_SECRET=tu-api-secret
```

Instala python-dotenv:
```bash
pip install python-dotenv
```

Y agrega al inicio de `app.py`:
```python
from dotenv import load_dotenv
load_dotenv()  # Carga variables del archivo .env
```

### En Render (producción):

1. Ve a tu Web Service en Render
2. Ve a **"Environment"** → **"Environment Variables"**
3. Agrega 3 variables:

| Key | Value |
|-----|-------|
| `CLOUDINARY_CLOUD_NAME` | tu-cloud-name |
| `CLOUDINARY_API_KEY` | 123456789012345 |
| `CLOUDINARY_API_SECRET` | abcdefgh1234567890abcdef |

4. Guarda y Render redeployará automáticamente

---

## 🚀 PASO 7: Eliminar static/uploads (opcional)

Con Cloudinary, ya no necesitas la carpeta `static/uploads/`. Puedes:

1. Eliminar la carpeta `static/uploads/`
2. Eliminar la función `allowed_file` si ya no la usas
3. Tu app queda más ligera

---

## ✅ Ventajas de Cloudinary

| Característica | Beneficio |
|----------------|-----------|
| **CDN Global** | Imágenes cargan rápido en cualquier país |
| **Optimización automática** | JPG/PNG/WebP según el navegador |
| **Redimensionamiento** | Subes una foto, Cloudinary la adapta |
| **Transformaciones** | Puedes pedir la imagen en cualquier tamaño |
| **Backup** | Tus imágenes están seguras en la nube |
| **Gratis** | Hasta 25GB de almacenamiento + 25GB de transferencia mensual |

---

## 💰 Precios de Cloudinary

| Plan | Almacenamiento | Transferencia | Costo |
|------|---------------|---------------|-------|
| **Free** | 25 GB | 25 GB/mes | **$0** |
| Plus | 225 GB | 225 GB/mes | $25/mes |
| Advanced | 500 GB | 500 GB/mes | $99/mes |

> Para tu MVP con 50-200 clientes, el plan **Free es más que suficiente**.

---

## 🧪 Ejemplo de URL transformada

Cloudinary permite pedir la imagen en diferentes tamaños:

```
Original:    https://res.cloudinary.com/tu-cloud/image/upload/abc123.jpg
Reducida:    https://res.cloudinary.com/tu-cloud/image/upload/w_300/abc123.jpg
Cuadrada:    https://res.cloudinary.com/tu-cloud/image/upload/w_300,h_300,c_fill/abc123.jpg
Optimizada:  https://res.cloudinary.com/tu-cloud/image/upload/q_auto,f_auto/abc123.jpg
```

Esto lo puedes usar en `profile.html` para mostrar thumbnails pequeños y la imagen grande al tocar.

---

## 📚 Recursos

- **Cloudinary Docs:** [cloudinary.com/documentation](https://cloudinary.com/documentation)
- **Python SDK:** [cloudinary.com/documentation/django_python_integration](https://cloudinary.com/documentation/django_python_integration)
- **Transformaciones:** [cloudinary.com/documentation/transformation_reference](https://cloudinary.com/documentation/transformation_reference)
