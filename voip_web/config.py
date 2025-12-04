import os
import yaml
from pathlib import Path


class Config:
    """Gestionnaire de configuration pour VoIP Web"""
    
    # Configuration par défaut
    DEFAULT_CONFIG = {
        'server': {
            'host': '0.0.0.0',
            'port': 5000,
            'debug': False,
            'secret_key': 'voip_secret_key_2024'
        },
        'ssl': {
            'enabled': True,
            'cert_file': 'cert.pem',
            'key_file': 'key.pem'
        },
        'socketio': {
            'cors_allowed_origins': '*',
            'ping_timeout': 60,
            'ping_interval': 25,
            'async_mode': 'eventlet'
        },
        'redis': {
            'enabled': False,
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None
        },
        'limits': {
            'max_users_per_room': 50,
            'max_message_length': 1000,
            'max_username_length': 30,
            'min_username_length': 2,
            'rate_limit_messages': 10
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'voip_server.log',
            'console': True
        },
        'features': {
            'audio_calls': True,
            'video_calls': True,
            'text_chat': True,
            'file_sharing': False,
            'screen_sharing': False
        },
        'webrtc': {
            'ice_servers': [
                {'urls': 'stun:stun.l.google.com:19302'},
                {'urls': 'stun:stun1.l.google.com:19302'}
            ]
        }
    }
    
    def __init__(self, config_file=None):
        """
        Initialise la configuration
        
        Args:
            config_file (str): Chemin vers le fichier de configuration YAML
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_file:
            self.load_from_file(config_file)
        
        # Surcharger avec les variables d'environnement
        self.load_from_env()
    
    def load_from_file(self, config_file):
        """Charge la configuration depuis un fichier YAML"""
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        self._merge_config(self.config, file_config)
                print(f"✓ Configuration chargée depuis {config_file}")
            else:
                print(f"⚠ Fichier de configuration non trouvé: {config_file}")
        except Exception as e:
            print(f"✗ Erreur lors du chargement de la configuration: {e}")
    
    def load_from_env(self):
        """Charge la configuration depuis les variables d'environnement"""
        # Serveur
        if os.getenv('VOIP_HOST'):
            self.config['server']['host'] = os.getenv('VOIP_HOST')
        if os.getenv('VOIP_PORT'):
            self.config['server']['port'] = int(os.getenv('VOIP_PORT'))
        if os.getenv('VOIP_SECRET_KEY'):
            self.config['server']['secret_key'] = os.getenv('VOIP_SECRET_KEY')
        if os.getenv('VOIP_DEBUG'):
            self.config['server']['debug'] = os.getenv('VOIP_DEBUG').lower() == 'true'
        
        # SSL
        if os.getenv('VOIP_SSL_ENABLED'):
            self.config['ssl']['enabled'] = os.getenv('VOIP_SSL_ENABLED').lower() == 'true'
        if os.getenv('VOIP_SSL_CERT'):
            self.config['ssl']['cert_file'] = os.getenv('VOIP_SSL_CERT')
        if os.getenv('VOIP_SSL_KEY'):
            self.config['ssl']['key_file'] = os.getenv('VOIP_SSL_KEY')
        
        # Redis
        if os.getenv('VOIP_REDIS_ENABLED'):
            self.config['redis']['enabled'] = os.getenv('VOIP_REDIS_ENABLED').lower() == 'true'
        if os.getenv('VOIP_REDIS_HOST'):
            self.config['redis']['host'] = os.getenv('VOIP_REDIS_HOST')
        if os.getenv('VOIP_REDIS_PORT'):
            self.config['redis']['port'] = int(os.getenv('VOIP_REDIS_PORT'))
        if os.getenv('VOIP_REDIS_PASSWORD'):
            self.config['redis']['password'] = os.getenv('VOIP_REDIS_PASSWORD')
    
    def _merge_config(self, base, update):
        """Fusionne récursivement deux dictionnaires de configuration"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, *keys, default=None):
        """
        Récupère une valeur de configuration
        
        Args:
            *keys: Chemin vers la valeur (ex: 'server', 'port')
            default: Valeur par défaut si non trouvée
            
        Returns:
            La valeur ou default
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, *keys, value):
        """
        Définit une valeur de configuration
        
        Args:
            *keys: Chemin vers la valeur
            value: Nouvelle valeur
        """
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
    
    def to_dict(self):
        """Retourne la configuration complète"""
        return self.config.copy()
    
    def save_to_file(self, config_file):
        """Sauvegarde la configuration dans un fichier YAML"""
        try:
            with open(config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            print(f"✓ Configuration sauvegardée dans {config_file}")
        except Exception as e:
            print(f"✗ Erreur lors de la sauvegarde: {e}")


# Instance globale de configuration
_global_config = None


def get_config(config_file=None):
    """Retourne l'instance globale de configuration"""
    global _global_config
    if _global_config is None:
        _global_config = Config(config_file)
    return _global_config


def reload_config(config_file=None):
    """Recharge la configuration"""
    global _global_config
    _global_config = Config(config_file)
    return _global_config