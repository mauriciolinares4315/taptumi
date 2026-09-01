"""Utilidades varias compartidas entre rutas."""
from app.config import config
from app.db import SOCIAL_ICONS


def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
    )


def attach_social_icon(link_dict: dict) -> dict:
    """Determina el icono de Font Awesome para un link social."""
    url_lower = (link_dict.get("url") or "").lower()

    icon_key = "default"
    for key in SOCIAL_ICONS:
        if key != "default" and key in url_lower:
            icon_key = key
            break

    if icon_key == "default":
        bd_icon = (link_dict.get("icon") or "default").lower().strip()
        if bd_icon in SOCIAL_ICONS:
            icon_key = bd_icon

    link_dict["fa_icon"] = SOCIAL_ICONS.get(icon_key, SOCIAL_ICONS["default"])
    link_dict["icon_key"] = icon_key 
    return link_dict
    
