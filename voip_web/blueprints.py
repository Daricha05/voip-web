from flask import Blueprint, render_template, jsonify
from .utils import get_local_ip, generate_qr_base64
from .config import get_config

# Blueprint principal
voip_bp = Blueprint(
    'voip',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/voip'
)

# Blueprint pour l'API
api_bp = Blueprint(
    'voip_api',
    __name__,
    url_prefix='/voip/api'
)


# === Routes Blueprint Principal ===

@voip_bp.route('/')
def index():
    """Page d'accueil avec QR code"""
    config = get_config()
    server_ip = get_local_ip()
    port = config.get('server', 'port', default=5000)
    
    protocol = 'https' if config.get('ssl', 'enabled') else 'http'
    server_url = f"{protocol}://{server_ip}:{port}/voip/chat"
    qr_code = generate_qr_base64(server_url)
    
    return render_template('index.html', 
                         server_ip=server_ip,
                         server_url=server_url,
                         qr_code=qr_code)


@voip_bp.route('/chat')
def chat():
    """Page de chat"""
    config = get_config()
    
    # Passer les configurations au template
    return render_template('chat.html',
                         audio_enabled=config.get('features', 'audio_calls'),
                         video_enabled=config.get('features', 'video_calls'),
                         max_message_length=config.get('limits', 'max_message_length'))


# === Routes API ===

@api_bp.route('/status')
def status():
    """Status du serveur"""
    config = get_config()
    return jsonify({
        'status': 'online',
        'version': '1.0.0',
        'features': config.get('features'),
        'limits': config.get('limits')
    })


@api_bp.route('/config')
def get_public_config():
    """Configuration publique (sans secrets)"""
    config = get_config()
    
    public_config = {
        'features': config.get('features'),
        'limits': {
            'max_users_per_room': config.get('limits', 'max_users_per_room'),
            'max_message_length': config.get('limits', 'max_message_length'),
            'max_username_length': config.get('limits', 'max_username_length'),
            'min_username_length': config.get('limits', 'min_username_length')
        },
        'webrtc': {
            'ice_servers': config.get('webrtc', 'ice_servers')
        }
    }
    
    return jsonify(public_config)


@api_bp.route('/rooms')
def list_rooms():
    """Liste des rooms actives (nécessite import de rooms)"""
    from .server import rooms
    
    room_list = []
    for room_name, user_sids in rooms.items():
        room_list.append({
            'name': room_name,
            'users': len(user_sids)
        })
    
    return jsonify({
        'rooms': room_list,
        'total': len(room_list)
    })


def register_blueprints(app):
    """Enregistre tous les blueprints dans l'application"""
    app.register_blueprint(voip_bp)
    app.register_blueprint(api_bp)
    print("✓ Blueprints VoIP enregistrés")