# ============================================
# Fonctions utilitaires (QR, IP, etc.)
# ============================================

import socket
import qrcode
import io
import base64


def get_local_ip():
    """Récupère l'IP locale de la machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return socket.gethostbyname(socket.gethostname())


def generate_qr_base64(url):
    """
    Génère un QR code en base64 pour une URL donnée
    
    Args:
        url (str): L'URL à encoder dans le QR code
        
    Returns:
        str: Image QR code encodée en base64
    """
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()


def validate_username(username):
    """
    Valide un nom d'utilisateur
    
    Args:
        username (str): Le nom à valider
        
    Returns:
        tuple: (bool, str) - (valide, message d'erreur)
    """
    if not username or not username.strip():
        return False, "Le nom d'utilisateur ne peut pas être vide"
    
    if len(username) < 2:
        return False, "Le nom d'utilisateur doit contenir au moins 2 caractères"
    
    if len(username) > 30:
        return False, "Le nom d'utilisateur ne peut pas dépasser 30 caractères"
    
    return True, ""


def sanitize_message(message):
    """
    Nettoie un message pour éviter les problèmes XSS
    
    Args:
        message (str): Le message à nettoyer
        
    Returns:
        str: Message nettoyé
    """
    if not message:
        return ""
    
    # Enlever les balises HTML basiques
    message = message.replace("<", "&lt;").replace(">", "&gt;")
    
    return message.strip()
