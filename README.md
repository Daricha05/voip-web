# 🌐 VoIP Web Server

Serveur de chat vocal et vidéo en temps réel basé sur Flask-SocketIO et WebRTC.

## ✨ Fonctionnalités

- 💬 **Chat texte en temps réel**
- 📞 **Appels audio WebRTC**
- 📹 **Appels vidéo WebRTC**
- 👥 **Gestion des rooms/salons**
- 📱 **QR code pour connexion mobile**
- 🔒 **Support SSL/HTTPS**
- 🗄️ **Stockage Redis optionnel**
- ⚙️ **Configuration flexible (YAML/ENV)**

## 🚀 Installation

### Installation via pip

```bash
pip install voip-web
```

### Installation depuis les sources

```bash
git clone https://github.com/Daricha05/voip-web.git
cd voip-web
pip install -e .
```

### Dépendances

```bash
pip install flask flask-socketio eventlet qrcode[pil] pyyaml
# Optionnel pour Redis
pip install redis
# Optionnel pour les tests
pip install pytest pytest-cov
```

## 📖 Utilisation rapide

### Démarrage simple

```bash
# Avec l'interface CLI
voip-web start

# Ou directement en Python
python -m voip_web.server
```

### Avec configuration personnalisée

```bash
# Générer un fichier de configuration
voip-web init-config

# Modifier config.yml puis démarrer
voip-web start --config config.yml
```

### Options de ligne de commande

```bash
voip-web start --host 0.0.0.0 --port 8080 --no-ssl --debug
```

## 🔧 Configuration

### Fichier config.yml

```yaml
server:
  host: "0.0.0.0"
  port: 5000
  debug: false
  secret_key: "your-secret-key"

ssl:
  enabled: true
  cert_file: "cert.pem"
  key_file: "key.pem"

redis:
  enabled: false
  host: "localhost"
  port: 6379

features:
  audio_calls: true
  video_calls: true
  text_chat: true
```

### Variables d'environnement

```bash
export VOIP_HOST="0.0.0.0"
export VOIP_PORT="5000"
export VOIP_SECRET_KEY="your-secret-key"
export VOIP_SSL_ENABLED="true"
export VOIP_REDIS_ENABLED="false"
```

## 🔐 Certificats SSL

### Génération automatique (dev)

```bash
voip-web generate-certs
```

### Certificats personnalisés

```yaml
ssl:
  enabled: true
  cert_file: "/path/to/cert.pem"
  key_file: "/path/to/key.pem"
```

## 🐳 Docker

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["voip-web", "start"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  voip-web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - VOIP_HOST=0.0.0.0
      - VOIP_PORT=5000
      - VOIP_REDIS_ENABLED=true
      - VOIP_REDIS_HOST=redis
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## 🔌 Intégration dans un projet existant

### Comme module

```python
from flask import Flask
from voip_web import create_app, socketio
from voip_web.blueprints import register_blueprints

app = Flask(__name__)

# Vos routes...
@app.route('/')
def home():
    return "Mon application"

# Enregistrer les blueprints VoIP
register_blueprints(app)

# Créer SocketIO
socketio.init_app(app)

if __name__ == '__main__':
    socketio.run(app)
```

### Avec Blueprint

```python
from flask import Flask
from voip_web.blueprints import voip_bp, api_bp

app = Flask(__name__)

# Enregistrer le blueprint avec un préfixe
app.register_blueprint(voip_bp, url_prefix='/voip')
app.register_blueprint(api_bp, url_prefix='/api')

# URLs disponibles:
# /voip/          -> Page d'accueil
# /voip/chat      -> Interface de chat
# /api/status     -> Statut du serveur
# /api/config     -> Configuration publique
```

## 🧪 Tests

### Exécuter les tests

```bash
# Tous les tests
pytest

# Avec couverture
pytest --cov=voip_web --cov-report=html

# Tests spécifiques
pytest tests/test_voip.py::test_config_default
```

### Tests manuels

```bash
# Tester la configuration
voip-web test

# Afficher la configuration
voip-web show-config

# Informations du serveur
voip-web info
```

## 📚 API

### Routes Web

- `GET /` - Page d'accueil avec QR code
- `GET /chat` - Interface de chat
- `GET /voip/api/status` - Statut du serveur (JSON)
- `GET /voip/api/config` - Configuration publique (JSON)
- `GET /voip/api/rooms` - Liste des rooms actives (JSON)

### Événements SocketIO

#### Client → Serveur

- `join` - Rejoindre une room
- `text_message` - Envoyer un message texte
- `call_user` - Initier un appel (audio/vidéo)
- `call_answer` - Répondre à un appel
- `webrtc_signal` - Signaux WebRTC (SDP/ICE)
- `hangup` - Raccrocher

#### Serveur → Client

- `join_success` - Confirmation de connexion
- `user_joined` - Nouvel utilisateur
- `user_left` - Utilisateur parti
- `user_list` - Liste des utilisateurs
- `text_message` - Nouveau message
- `incoming_call` - Appel entrant
- `call_accepted` - Appel accepté
- `call_rejected` - Appel refusé
- `call_ended` - Appel terminé
- `webrtc_signal` - Signaux WebRTC

## 🏗️ Architecture

```
voip-web/
├── voip_web/
│   ├── __init__.py          # Package principal
│   ├── server.py            # Serveur Flask/SocketIO
│   ├── config.py            # Gestion configuration
│   ├── storage.py           # Backends de stockage
│   ├── blueprints.py        # Blueprints Flask
│   ├── utils.py             # Utilitaires
│   ├── cli.py               # Interface CLI
│   └── templates/           # Templates HTML
│       ├── index.html
│       └── chat.html
├── tests/
│   └── test_voip.py         # Tests unitaires
├── config.yml               # Configuration par défaut
├── setup.py                 # Configuration du package
├── requirements.txt         # Dépendances
└── README.md               # Documentation
```

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- [Flask](https://flask.palletsprojects.com/) - Framework web
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/) - WebSocket
- [WebRTC](https://webrtc.org/) - Communication temps réel
- [Eventlet](https://eventlet.net/) - Programmation concurrente

## 📞 Support

- 📧 Email: johnnyricharde5@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/Daricha/voip-web/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/Daricha/voip-web/discussions)

## 🗺️ Roadmap

- [ ] Partage d'écran
- [ ] Partage de fichiers
- [ ] Enregistrement des appels
- [ ] Support multi-langues
- [ ] Application mobile
- [ ] Chiffrement end-to-end
- [ ] Modération avancée

---

**Fait avec ❤️ par Johnny Richard**