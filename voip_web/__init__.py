"""
VoIP Web - Serveur de chat vocal et vidéo avec Flask-SocketIO
"""

from .server import create_app, socketio
from .utils import get_local_ip, generate_qr_base64

__version__ = "1.0.0"
__all__ = ["create_app", "socketio", "get_local_ip", "generate_qr_base64"]


# Configuration par défaut
DEFAULT_CONFIG = {
    'SECRET_KEY': 'voip_secret_key_2024',
    'CORS_ALLOWED_ORIGINS': "*",
    'PING_TIMEOUT': 60,
    'PING_INTERVAL': 25,
    'HOST': '0.0.0.0',
    'PORT': 5000,
    'SSL_CERT': 'cert.pem',
    'SSL_KEY': 'key.pem',
}
