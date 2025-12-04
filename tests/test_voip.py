import pytest
from voip_web import create_app, socketio
from voip_web.config import Config
from voip_web.utils import get_local_ip, generate_qr_base64, validate_username, sanitize_message
from voip_web.storage import MemoryStorage


# === Fixtures ===

@pytest.fixture
def app():
    """Crée une instance de l'app pour les tests"""
    config = {
        'TESTING': True,
        'SECRET_KEY': 'test_key' 
    }
    app = create_app(config)
    return app


@pytest.fixture
def client(app):
    """Client de test Flask"""
    return app.test_client()


@pytest.fixture
def socketio_client(app):
    """Client SocketIO de test"""
    return socketio.test_client(app)


@pytest.fixture
def storage():
    """Instance de stockage pour les tests"""
    return MemoryStorage()


# === Tests Configuration ===

def test_config_default():
    """Test de la configuration par défaut"""
    cfg = Config()
    
    assert cfg.get('server', 'port') == 5000
    assert cfg.get('server', 'host') == '0.0.0.0'
    assert cfg.get('features', 'audio_calls') is True
    assert cfg.get('features', 'video_calls') is True


def test_config_get_set():
    """Test des getters/setters de config"""
    cfg = Config()
    
    cfg.set('server', 'port', value=8080)
    assert cfg.get('server', 'port') == 8080
    
    cfg.set('custom', 'key', value='value')
    assert cfg.get('custom', 'key') == 'value'


def test_config_merge():
    """Test de la fusion de configs"""
    cfg = Config()
    
    custom_config = {
        'server': {
            'port': 3000
        },
        'new_section': {
            'key': 'value'
        }
    }
    
    cfg._merge_config(cfg.config, custom_config)
    
    assert cfg.get('server', 'port') == 3000
    assert cfg.get('server', 'host') == '0.0.0.0'  # Conservé
    assert cfg.get('new_section', 'key') == 'value'


# === Tests Utils ===

def test_get_local_ip():
    """Test de récupération de l'IP locale"""
    ip = get_local_ip()
    
    assert ip is not None
    assert isinstance(ip, str)
    assert len(ip.split('.')) == 4  # Format IPv4


def test_generate_qr_base64():
    """Test de génération de QR code"""
    url = "https://example.com"
    qr_base64 = generate_qr_base64(url)
    
    assert qr_base64 is not None
    assert isinstance(qr_base64, str)
    assert len(qr_base64) > 100  # Le base64 doit être assez long


def test_validate_username():
    """Test de validation des noms d'utilisateur"""
    # Valides
    assert validate_username("Alice")[0] is True
    assert validate_username("Bob123")[0] is True
    assert validate_username("User_Name")[0] is True
    
    # Invalides
    assert validate_username("")[0] is False
    assert validate_username("A")[0] is False  # Trop court
    assert validate_username("A" * 50)[0] is False  # Trop long
    assert validate_username("   ")[0] is False  # Vide


def test_sanitize_message():
    """Test de nettoyage des messages"""
    # HTML doit être échappé
    assert sanitize_message("<script>alert('xss')</script>") == "&lt;script&gt;alert('xss')&lt;/script&gt;"
    assert sanitize_message("<b>Bold</b>") == "&lt;b&gt;Bold&lt;/b&gt;"
    
    # Texte normal doit rester intact
    assert sanitize_message("Hello World") == "Hello World"
    
    # Espaces doivent être nettoyés
    assert sanitize_message("  Test  ") == "Test"


# === Tests Storage ===

def test_memory_storage_users(storage):
    """Test du stockage des utilisateurs"""
    storage.set_user('sid1', {'name': 'Alice', 'room': 'lobby'})
    storage.set_user('sid2', {'name': 'Bob', 'room': 'lobby'})
    
    assert storage.get_user('sid1')['name'] == 'Alice'
    assert storage.get_user('sid2')['name'] == 'Bob'
    
    users = storage.get_users()
    assert len(users) == 2
    
    storage.delete_user('sid1')
    assert storage.get_user('sid1') is None
    assert len(storage.get_users()) == 1


def test_memory_storage_rooms(storage):
    """Test du stockage des rooms"""
    storage.add_user_to_room('lobby', 'sid1')
    storage.add_user_to_room('lobby', 'sid2')
    storage.add_user_to_room('room2', 'sid3')
    
    lobby_users = storage.get_room('lobby')
    assert len(lobby_users) == 2
    assert 'sid1' in lobby_users
    assert 'sid2' in lobby_users
    
    room2_users = storage.get_room('room2')
    assert len(room2_users) == 1
    assert 'sid3' in room2_users
    
    storage.remove_user_from_room('lobby', 'sid1')
    assert len(storage.get_room('lobby')) == 1
    
    storage.delete_room('lobby')
    assert len(storage.get_room('lobby')) == 0


# === Tests Routes Flask ===

def test_index_route(client):
    """Test de la page d'accueil"""
    response = client.get('/')
    
    assert response.status_code == 200
    assert b'VoIP' in response.data


def test_chat_route(client):
    """Test de la page de chat"""
    response = client.get('/chat')
    
    assert response.status_code == 200
    assert b'chat' in response.data.lower()


def test_api_status(client):
    """Test de l'API status"""
    response = client.get('/voip/api/status')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'online'
    assert 'version' in data


def test_api_config(client):
    """Test de l'API config publique"""
    response = client.get('/voip/api/config')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'features' in data
    assert 'limits' in data
    assert 'webrtc' in data


# === Tests SocketIO ===

def test_socketio_connect(socketio_client):
    """Test de connexion SocketIO"""
    assert socketio_client.is_connected()


def test_socketio_join(socketio_client):
    """Test de rejoindre une room"""
    socketio_client.emit('join', {
        'username': 'TestUser',
        'room': 'test_room'
    })
    
    received = socketio_client.get_received()
    
    # Vérifier qu'on reçoit les événements attendus
    event_types = [msg['name'] for msg in received]
    assert 'join_success' in event_types
    assert 'user_list' in event_types


def test_socketio_text_message(socketio_client):
    """Test d'envoi de message texte"""
    # D'abord rejoindre
    socketio_client.emit('join', {
        'username': 'TestUser',
        'room': 'test_room'
    })
    socketio_client.get_received()  # Nettoyer
    
    # Envoyer un message
    socketio_client.emit('text_message', {
        'message': 'Hello World'
    })
    
    received = socketio_client.get_received()
    
    # Vérifier qu'on reçoit le message
    text_messages = [msg for msg in received if msg['name'] == 'text_message']
    assert len(text_messages) > 0
    assert text_messages[0]['args'][0]['message'] == 'Hello World'


def test_socketio_disconnect(socketio_client):
    """Test de déconnexion"""
    socketio_client.emit('join', {
        'username': 'TestUser',
        'room': 'test_room'
    })
    
    socketio_client.disconnect()
    assert not socketio_client.is_connected()


# === Tests d'intégration ===

def test_full_chat_flow(socketio_client):
    """Test d'un flux complet de chat"""
    
    # 1. Connexion
    assert socketio_client.is_connected()
    
    # 2. Rejoindre la room
    socketio_client.emit('join', {
        'username': 'Alice',
        'room': 'lobby'
    })
    
    received = socketio_client.get_received()
    assert any(msg['name'] == 'join_success' for msg in received)
    
    # 3. Envoyer un message
    socketio_client.emit('text_message', {
        'message': 'Hello everyone!'
    })
    
    received = socketio_client.get_received()
    text_msg = next((msg for msg in received if msg['name'] == 'text_message'), None)
    assert text_msg is not None
    assert text_msg['args'][0]['username'] == 'Alice'
    
    # 4. Déconnexion
    socketio_client.disconnect()
    assert not socketio_client.is_connected()


# === Tests de limites ===

def test_username_length_limits():
    """Test des limites de longueur de username"""
    cfg = Config()
    max_len = cfg.get('limits', 'max_username_length')
    min_len = cfg.get('limits', 'min_username_length')
    
    # Nom trop court
    short_name = 'A' * (min_len - 1)
    assert validate_username(short_name)[0] is False
    
    # Nom valide
    valid_name = 'A' * min_len
    assert validate_username(valid_name)[0] is True
    
    # Nom trop long
    long_name = 'A' * (max_len + 1)
    assert validate_username(long_name)[0] is False


def test_message_sanitization():
    """Test de la sanitisation des messages"""
    dangerous_inputs = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "<iframe src='javascript:alert(1)'>",
    ]
    
    for dangerous in dangerous_inputs:
        sanitized = sanitize_message(dangerous)
        assert '<' not in sanitized
        assert '>' not in sanitized


# === Exécution des tests ===

if __name__ == '__main__':
    pytest.main([__file__, '-v'])