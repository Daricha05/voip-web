"""
VoIP Web - Serveur de chat vocal et vidéo avec Flask-SocketIO
"""

__version__ = "1.0.0"
__all__ = ["create_app", "socketio", "get_local_ip", "generate_qr_base64"]

# Import paresseux pour éviter les dépendances circulaires
def create_app(config=None):
    from .server import create_app as _create_app
    return _create_app(config)

def get_socketio():
    from .server import socketio
    return socketio

def get_local_ip():
    from .utils import get_local_ip as _get_local_ip
    return _get_local_ip()

def generate_qr_base64(url):
    from .utils import generate_qr_base64 as _generate_qr_base64
    return _generate_qr_base64(url)