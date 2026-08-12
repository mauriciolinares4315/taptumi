#!/bin/bash
# ============================================================
# SCRIPT: Empaquetar proyecto NFC con venv
# ============================================================
# Guarda este archivo como "setup.sh" en la carpeta del proyecto
# y ejecútalo: bash setup.sh

echo "🚀 Configurando entorno virtual para NFC Profile App..."

# 1. Crear entorno virtual
echo "📦 Creando entorno virtual (venv)..."
python3 -m venv venv

# 2. Activar entorno virtual
echo "⚡ Activando entorno virtual..."
source venv/bin/activate

# 3. Instalar dependencias
echo "📥 Instalando dependencias desde requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Verificar instalación
echo "✅ Verificando instalación..."
python -c "import flask; print(f'Flask {flask.__version__} instalado')"
python -c "import flask_cors; print('Flask-CORS instalado')"

# 5. Crear script de activación
cat > run.sh << 'EOF'
#!/bin/bash
echo "🚀 Iniciando NFC Profile App..."
source venv/bin/activate
python app.py
EOF
chmod +x run.sh

echo ""
echo "=========================================="
echo "✅ ¡ENTORNO LISTO!"
echo "=========================================="
echo ""
echo "Para activar el entorno manualmente:"
echo "  source venv/bin/activate"
echo ""
echo "Para correr la app:"
echo "  bash run.sh"
echo "  o"
echo "  python app.py"
echo ""
echo "Para desactivar el entorno:"
echo "  deactivate"
echo ""
