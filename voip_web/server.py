# ============================================
# Code Flask/SocketIO
# ============================================

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import eventlet
import eventlet.wsgi
from eventlet import greenio

from .utils import get_local_ip, generate_qr_base64

# Stockage global (peut être remplacé par Redis en production)
users = {}
rooms = {}

def create_app(config=None):
    """Factory pattern pour créer l'application Flask"""
    app = Flask(__name__)
    
    # Configuration par défaut
    app.config['SECRET_KEY'] = 'voip_secret_key_2024'
    
    # Configuration personnalisée
    if config:
        app.config.update(config)
    
    return app

def create_socketio(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25):
    """Crée l'instance SocketIO"""
    return SocketIO(
        app, 
        cors_allowed_origins=cors_allowed_origins,
        ping_timeout=ping_timeout,
        ping_interval=ping_interval
    )

# Initialisation par défaut
app = create_app()
socketio = create_socketio(app)

# === ROUTES WEB ===
@app.route('/')
def index():
    """Page d'accueil avec QR code"""
    server_ip = get_local_ip()
    server_url = f"https://{server_ip}:5000/chat"
    qr_code = generate_qr_base64(server_url)
    
    return render_template('index.html', 
                         server_ip=server_ip,
                         server_url=server_url,
                         qr_code=qr_code)

@app.route('/chat')
def chat():
    """Page de chat"""
    return render_template('chat.html')

# === ÉVÉNEMENTS WEBSOCKET ===
@socketio.on('connect')
def handle_connect():
    """Nouvelle connexion"""
    print(f"✓ Client connecté: {request.sid}")
    emit('server_message', {'msg': 'Connecté au serveur'})

@socketio.on('disconnect')
def handle_disconnect():
    """Déconnexion"""
    sid = request.sid
    if sid in users:
        user = users[sid]
        username = user['name']
        room = user.get('room')
        
        if room and room in rooms:
            if sid in rooms[room]:
                rooms[room].remove(sid)
            
            emit('user_left', {
                'username': username,
                'users': [users[s]['name'] for s in rooms[room] if s in users]
            }, room=room)
            
            if not rooms[room]:
                del rooms[room]
        
        del users[sid]
        print(f"✗ {username} déconnecté")

@socketio.on('join')
def handle_join(data):
    """Utilisateur rejoint le chat"""
    sid = request.sid
    username = data.get('username', 'Anonymous')
    room = data.get('room', 'lobby')
    
    users[sid] = {'name': username, 'room': room}
    
    join_room(room)
    if room not in rooms:
        rooms[room] = []
    rooms[room].append(sid)
    
    emit('join_success', {'username': username, 'room': room})
    
    emit('user_joined', {
        'username': username,
        'users': [users[s]['name'] for s in rooms[room] if s in users]
    }, room=room, include_self=False)
    
    emit('user_list', {
        'users': [users[s]['name'] for s in rooms[room] if s in users]
    })
    
    print(f"✓ {username} a rejoint {room}")

@socketio.on('text_message')
def handle_text_message(data):
    """Message texte"""
    sid = request.sid
    if sid not in users:
        return
    
    username = users[sid]['name']
    room = users[sid]['room']
    message = data.get('message', '')
    timestamp = datetime.now().strftime('%H:%M')
    
    emit('text_message', {
        'username': username,
        'message': message,
        'timestamp': timestamp
    }, room=room)
    
    print(f"💬 [{room}] {username}: {message}")

@socketio.on('call_user')
def handle_call(data):
    """Appel vers un utilisateur"""
    sid = request.sid
    if sid not in users:
        return
    
    caller = users[sid]['name']
    target = data.get('target')
    call_type = data.get('call_type', 'audio')
    room = users[sid]['room']
    
    target_sid = None
    for s, u in users.items():
        if u['name'] == target and u['room'] == room:
            target_sid = s
            break
    
    if target_sid:
        emit('incoming_call', {
            'caller': caller,
            'call_type': call_type
        }, room=target_sid)
        print(f"📞 {caller} appelle {target} ({call_type})")

@socketio.on('call_answer')
def handle_call_answer(data):
    """Réponse à un appel"""
    sid = request.sid
    if sid not in users:
        return
    
    answerer = users[sid]['name']
    caller_name = data.get('caller')
    accepted = data.get('accepted', False)
    call_type = data.get('call_type', 'audio')
    room = users[sid]['room']
    
    caller_sid = None
    for s, u in users.items():
        if u['name'] == caller_name and u['room'] == room:
            caller_sid = s
            break
    
    if caller_sid:
        if accepted:
            emit('call_accepted', {
                'answerer': answerer,
                'call_type': call_type
            }, room=caller_sid)
            print(f"✅ {answerer} accepte l'appel {call_type} de {caller_name}")
        else:
            emit('call_rejected', {'answerer': answerer}, room=caller_sid)
            print(f"❌ {answerer} refuse l'appel de {caller_name}")

@socketio.on('webrtc_signal')
def handle_webrtc_signal(data):
    """Signal WebRTC"""
    sid = request.sid
    if sid not in users:
        return
    
    target = data.get('target')
    signal = data.get('signal')
    room = users[sid]['room']
    sender = users[sid]['name']
    
    target_sid = None
    for s, u in users.items():
        if u['name'] == target and u['room'] == room:
            target_sid = s
            break
    
    if target_sid:
        emit('webrtc_signal', {
            'sender': sender,
            'signal': signal
        }, room=target_sid)

@socketio.on('hangup')
def handle_hangup(data):
    """Raccrochage"""
    sid = request.sid
    if sid not in users:
        return
    
    username = users[sid]['name']
    target = data.get('target')
    room = users[sid]['room']
    
    target_sid = None
    for s, u in users.items():
        if u['name'] == target and u['room'] == room:
            target_sid = s
            break
    
    if target_sid:
        emit('call_ended', {'username': username}, room=target_sid)
    
    print(f"📴 {username} raccroche")

def main():
    """Point d'entrée pour la ligne de commande"""
    server_ip = get_local_ip()
    port = 5000
    
    print("\n" + "="*60)
    print("🌐 SERVEUR WEB VOIP DÉMARRÉ")
    print("="*60)
    print(f"📡 IP: {server_ip}")
    print(f"🌍 Port: {port}")
    print(f"🔗 URL locale: https://{server_ip}:{port}")
    print(f"📱 URL chat: https://{server_ip}:{port}/chat")
    print("="*60)
    print("✅ Scannez le QR code sur la page d'accueil !")
    print("="*60 + "\n")
    
    context = eventlet.wrap_ssl(
        eventlet.listen((server_ip, port)),
        certfile='cert.pem',
        keyfile='key.pem',
        server_side=True
    )

    eventlet.wsgi.server(context, app)

if __name__ == '__main__':
    main()
