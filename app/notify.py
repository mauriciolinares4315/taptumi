"""
Notificaciones al administrador. Se usan para avisar al admin cuando
un usuario solicita resetear su contraseña, y otros avisos futuros.

Todas las funciones son "fail silent": si las variables de entorno no
están configuradas o el servicio falla, la app sigue funcionando. El
error se registra en el log pero no rompe la operación del usuario.
"""
import logging
import os

import requests


def notify_admin_telegram(texto: str) -> bool:
    """
    Envía un mensaje al chat de Telegram del admin.

    Configuración necesaria en .env:
        TELEGRAM_BOT_TOKEN=...
        TELEGRAM_CHAT_ID=...

    Retorna True si se envió, False en caso contrario (no lanza).
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logging.info("Telegram no configurado, se omite notificación")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            logging.warning(
                f"Telegram respondió {r.status_code}: {r.text[:200]}"
            )
            return False
        return True
    except Exception as e:
        logging.warning(f"Telegram falló: {e}")
        return False


def notify_admin_solicitud_reset(slug: str, name: str, contact: str, message: str = "") -> bool:
    """Notificación formateada para una solicitud de reset de contraseña."""
    # Escapamos HTML básico para que Telegram no interprete caracteres raros
    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    texto = (
        f"🔐 <b>Solicitud de reset de contraseña</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Nombre:</b> {esc(name)}\n"
        f"📇 <b>Perfil:</b> /{esc(slug)}\n"
        f"📞 <b>Contacto:</b> {esc(contact)}\n"
    )
    if message:
        texto += f"💬 <b>Mensaje:</b> {esc(message)}\n"
    texto += "\n👉 Revisa el panel: /superadmin"

    return notify_admin_telegram(texto)