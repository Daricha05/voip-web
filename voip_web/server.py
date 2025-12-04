from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import eventlet
import eventlet.wsgi

from .utils import get_local_ip, generate_qr_base64
from .config import get_config
from .storage import get_storage
from .blueprints import register_blueprints

# Instances globales
app = None
socketio = None


def create_app(config=None):
    """Factory pattern pour créer l'application Flask"""
    global app
    
    app = Flask(__name__)
    
    # Configuration par défaut
    app.config['SECRET_KEY'] = 'voip_secret_key_2024'
    
    # Configuration personnalisée
    if config:
        app.config.update(config)
    
    # Enregistrer les blueprints
    register_blueprints(app)
    
    return app


def create_socketio(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25):
    """Crée l'instance SocketIO"""
    global socketio
    
    socketio = SocketIO(
        app, 
        cors_allowed_origins=cors_allowed_origins,
        ping_timeout=ping_timeout,
        ping_interval=ping_interval
    )
    
    return socketio


def register_socketio_handlers(socketio_instance):
    """Enregistre tous les handlers SocketIO"""
    
    storage = get_storage()
    
    @socketio_instance.on('connect')
    def handle_connect():
        """Nouvelle connexion"""
        print(f"✓ Client connecté: {request.sid}")
        emit('server_message', {'msg': 'Connecté au serveur'})

    @socketio_instance.on('disconnect')
    def handle_disconnect():
        """Déconnexion"""
        sid = request.sid
        user = storage.get_user(sid)
        
        if user:
            username = user['name']
            room = user.get('room')
            
            if room:
                room_users = storage.get_room(room)
                if sid in room_users:
                    storage.remove_user_from_room(room, sid)
                
                # Notifier les autres
                remaining_users = [
                    storage.get_user(s)['name'] 
                    for s in storage.get_room(room) 
                    if storage.get_user(s)
                ]
                
                emit('user_left', {
                    'username': username,
                    'users': remaining_users
                }, room=room)
                
                # Supprimer la room si vide
                if not storage.get_room(room):
                    storage.delete_room(room)
            
            storage.delete_user(sid)
            print(f"✗ {username} déconnecté")

    @socketio_instance.on('join')
    def handle_join(data):
        """Utilisateur rejoint le chat"""
        sid = request.sid
        username = data.get('username', 'Anonymous')
        room = data.get('room', 'lobby')
        
        # Vérifier les limites
        config = get_config()
        max_users = config.get('limits', 'max_users_per_room')
        
        if len(storage.get_room(room)) >= max_users:
            emit('error', {'msg': 'Room pleine'})
            return
        
        # Enregistrer l'utilisateur
        storage.set_user(sid, {
            'name': username,
            'room': room
        })
        
        # Ajouter à la room
        join_room(room)
        storage.add_user_to_room(room, sid)
        
        # Notifier l'utilisateur
        emit('join_success', {
            'username': username,
            'room': room
        })
        
        # Notifier les autres
        room_users = [
            storage.get_user(s)['name'] 
            for s in storage.get_room(room) 
            if storage.get_user(s)
        ]
        
        emit('user_joined', {
            'username': username,
            'users': room_users
        }, room=room, include_self=False)
        
        # Envoyer la liste des utilisateurs
        emit('user_list', {'users': room_users})
        
        print(f"✓ {username} a rejoint {room}")

    @socketio_instance.on('text_message')
    def handle_text_message(data):
        """Message texte"""
        sid = request.sid
        user = storage.get_user(sid)
        
        if not user:
            return
        
        username = user['name']
        room = user['room']
        message = data.get('message', '')
        
        # Vérifier la longueur
        config = get_config()
        max_length = config.get('limits', 'max_message_length')
        
        if len(message) > max_length:
            emit('error', {'msg': 'Message trop long'})
            return
        
        timestamp = datetime.now().strftime('%H:%M')
        
        # Broadcast à la room
        emit('text_message', {
            'username': username,
            'message': message,
            'timestamp': timestamp
        }, room=room)
        
        print(f"[{room}] {username}: {message}")

    @socketio_instance.on('call_user')
    def handle_call(data):
        """Appel vers un utilisateur"""
        sid = request.sid
        caller = storage.get_user(sid)
        
        if not caller:
            return
        
        caller_name = caller['name']
        target = data.get('target')
        call_type = data.get('call_type', 'audio')
        room = caller['room']
        
        # Vérifier que les appels sont activés
        config = get_config()
        if call_type == 'audio' and not config.get('features', 'audio_calls'):
            emit('error', {'msg': 'Appels audio désactivés'})
            return
        if call_type == 'video' and not config.get('features', 'video_calls'):
            emit('error', {'msg': 'Appels vidéo désactivés'})
            return
        
        # Trouver le destinataire
        target_sid = None
        for s in storage.get_room(room):
            u = storage.get_user(s)
            if u and u['name'] == target:
                target_sid = s
                break
        
        if target_sid:
            emit('incoming_call', {
                'caller': caller_name,
                'call_type': call_type
            }, room=target_sid)
            print(f"{caller_name} appelle {target} ({call_type})")

    @socketio_instance.on('call_answer')
    def handle_call_answer(data):
        """Réponse à un appel"""
        sid = request.sid
        answerer = storage.get_user(sid)
        
        if not answerer:
            return
        
        answerer_name = answerer['name']
        caller_name = data.get('caller')
        accepted = data.get('accepted', False)
        call_type = data.get('call_type', 'audio')
        room = answerer['room']
        
        # Trouver l'appelant
        caller_sid = None
        for s in storage.get_room(room):
            u = storage.get_user(s)
            if u and u['name'] == caller_name:
                caller_sid = s
                break
        
        if caller_sid:
            if accepted:
                emit('call_accepted', {
                    'answerer': answerer_name,
                    'call_type': call_type
                }, room=caller_sid)
                print(f"{answerer_name} accepte l'appel {call_type}")
            else:
                emit('call_rejected', {
                    'answerer': answerer_name
                }, room=caller_sid)
                print(f"{answerer_name} refuse l'appel")

    @socketio_instance.on('webrtc_signal')
    def handle_webrtc_signal(data):
        """Signal WebRTC"""
        sid = request.sid
        sender = storage.get_user(sid)
        
        if not sender:
            return
        
        target = data.get('target')
        signal = data.get('signal')
        room = sender['room']
        sender_name = sender['name']
        
        # Trouver le destinataire
        target_sid = None
        for s in storage.get_room(room):
            u = storage.get_user(s)
            if u and u['name'] == target:
                target_sid = s
                break
        
        if target_sid:
            emit('webrtc_signal', {
                'sender': sender_name,
                'signal': signal
            }, room=target_sid)

    @socketio_instance.on('hangup')
    def handle_hangup(data):
        """Raccrochage"""
        sid = request.sid
        user = storage.get_user(sid)
        
        if not user:
            return
        
        username = user['name']
        target = data.get('target')
        room = user['room']
        
        # Notifier le destinataire
        target_sid = None
        for s in storage.get_room(room):
            u = storage.get_user(s)
            if u and u['name'] == target:
                target_sid = s
                break
        
        if target_sid:
            emit('call_ended', {
                'username': username
            }, room=target_sid)
        
        print(f"📴 {username} raccroche")


def main():
    """Point d'entrée principal"""
    config = get_config()
    
    # Créer l'app et socketio
    app = create_app(config.to_dict())
    socketio = create_socketio(
        app,
        cors_allowed_origins=config.get('socketio', 'cors_allowed_origins'),
        ping_timeout=config.get('socketio', 'ping_timeout'),
        ping_interval=config.get('socketio', 'ping_interval')
    )
    
    # Enregistrer les handlers
    register_socketio_handlers(socketio)
    
    # Informations de démarrage
    server_ip = get_local_ip()
    port = config.get('server', 'port')
    ssl_enabled = config.get('ssl', 'enabled')
    
    protocol = 'https' if ssl_enabled else 'http'
    
    print("\n" + "="*60)
    print("SERVEUR WEB VOIP DÉMARRÉ")
    print("="*60)
    print(f"IP: {server_ip}")
    print(f"Port: {port}")
    print(f"URL locale: {protocol}://{server_ip}:{port}")
    print(f"URL chat: {protocol}://{server_ip}:{port}/chat")
    print("="*60)
    print("Scannez le QR code sur la page d'accueil !")
    print("="*60 + "\n")
    
    # Démarrer le serveur
    if ssl_enabled:
        cert_file = config.get('ssl', 'cert_file')
        key_file = config.get('ssl', 'key_file')
        
        context = eventlet.wrap_ssl(
            eventlet.listen((server_ip, port)),
            certfile=cert_file,
            keyfile=key_file,
            server_side=True
        )
        eventlet.wsgi.server(context, app)
    else:
        socketio.run(
            app,
            host=server_ip,
            port=port,
            debug=config.get('server', 'debug')
        )


if __name__ == '__main__':
    main()