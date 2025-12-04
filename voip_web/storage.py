import json
from abc import ABC, abstractmethod
from .config import get_config

# Stockage en mémoire par défaut
_memory_users = {}
_memory_rooms = {}


class StorageBackend(ABC):
    """Interface abstraite pour les backends de stockage"""
    
    @abstractmethod
    def get_users(self):
        """Récupère tous les utilisateurs"""
        pass
    
    @abstractmethod
    def get_user(self, sid):
        """Récupère un utilisateur par SID"""
        pass
    
    @abstractmethod
    def set_user(self, sid, user_data):
        """Enregistre un utilisateur"""
        pass
    
    @abstractmethod
    def delete_user(self, sid):
        """Supprime un utilisateur"""
        pass
    
    @abstractmethod
    def get_rooms(self):
        """Récupère toutes les rooms"""
        pass
    
    @abstractmethod
    def get_room(self, room_name):
        """Récupère une room"""
        pass
    
    @abstractmethod
    def add_user_to_room(self, room_name, sid):
        """Ajoute un utilisateur à une room"""
        pass
    
    @abstractmethod
    def remove_user_from_room(self, room_name, sid):
        """Retire un utilisateur d'une room"""
        pass
    
    @abstractmethod
    def delete_room(self, room_name):
        """Supprime une room"""
        pass


class MemoryStorage(StorageBackend):
    """Stockage en mémoire (par défaut)"""
    
    def __init__(self):
        self.users = _memory_users
        self.rooms = _memory_rooms
    
    def get_users(self):
        return self.users
    
    def get_user(self, sid):
        return self.users.get(sid)
    
    def set_user(self, sid, user_data):
        self.users[sid] = user_data
    
    def delete_user(self, sid):
        if sid in self.users:
            del self.users[sid]
    
    def get_rooms(self):
        return self.rooms
    
    def get_room(self, room_name):
        return self.rooms.get(room_name, [])
    
    def add_user_to_room(self, room_name, sid):
        if room_name not in self.rooms:
            self.rooms[room_name] = []
        if sid not in self.rooms[room_name]:
            self.rooms[room_name].append(sid)
    
    def remove_user_from_room(self, room_name, sid):
        if room_name in self.rooms and sid in self.rooms[room_name]:
            self.rooms[room_name].remove(sid)
    
    def delete_room(self, room_name):
        if room_name in self.rooms:
            del self.rooms[room_name]


class RedisStorage(StorageBackend):
    """Stockage Redis pour sessions distribuées"""
    
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        try:
            import redis
            self.redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True
            )
            # Test de connexion
            self.redis.ping()
            print(f"✓ Connecté à Redis: {host}:{port}")
        except ImportError:
            raise ImportError("Le package 'redis' est requis. Installez-le avec: pip install redis")
        except Exception as e:
            raise ConnectionError(f"Impossible de se connecter à Redis: {e}")
    
    def _user_key(self, sid):
        return f"voip:user:{sid}"
    
    def _room_key(self, room_name):
        return f"voip:room:{room_name}"
    
    def get_users(self):
        """Note: Cette méthode est coûteuse avec Redis"""
        users = {}
        for key in self.redis.scan_iter("voip:user:*"):
            sid = key.split(":")[-1]
            user_data = self.redis.get(key)
            if user_data:
                users[sid] = json.loads(user_data)
        return users
    
    def get_user(self, sid):
        user_data = self.redis.get(self._user_key(sid))
        return json.loads(user_data) if user_data else None
    
    def set_user(self, sid, user_data):
        self.redis.set(self._user_key(sid), json.dumps(user_data))
        # TTL de 24h pour nettoyer les sessions abandonnées
        self.redis.expire(self._user_key(sid), 86400)
    
    def delete_user(self, sid):
        self.redis.delete(self._user_key(sid))
    
    def get_rooms(self):
        """Note: Cette méthode est coûteuse avec Redis"""
        rooms = {}
        for key in self.redis.scan_iter("voip:room:*"):
            room_name = key.split(":", 2)[-1]
            rooms[room_name] = list(self.redis.smembers(key))
        return rooms
    
    def get_room(self, room_name):
        return list(self.redis.smembers(self._room_key(room_name)))
    
    def add_user_to_room(self, room_name, sid):
        self.redis.sadd(self._room_key(room_name), sid)
        # TTL de 24h
        self.redis.expire(self._room_key(room_name), 86400)
    
    def remove_user_from_room(self, room_name, sid):
        self.redis.srem(self._room_key(room_name), sid)
    
    def delete_room(self, room_name):
        self.redis.delete(self._room_key(room_name))
    
    def get_room_count(self, room_name):
        """Nombre d'utilisateurs dans une room"""
        return self.redis.scard(self._room_key(room_name))


# Instance globale
_storage = None


def get_storage():
    """Retourne l'instance de stockage appropriée"""
    global _storage
    
    if _storage is None:
        config = get_config()
        
        if config.get('redis', 'enabled'):
            try:
                _storage = RedisStorage(
                    host=config.get('redis', 'host'),
                    port=config.get('redis', 'port'),
                    db=config.get('redis', 'db'),
                    password=config.get('redis', 'password')
                )
                print("✓ Utilisation du stockage Redis")
            except Exception as e:
                print(f"⚠ Erreur Redis, utilisation du stockage mémoire: {e}")
                _storage = MemoryStorage()
        else:
            _storage = MemoryStorage()
            print("✓ Utilisation du stockage mémoire")
    
    return _storage


def reset_storage():
    """Réinitialise le stockage"""
    global _storage
    _storage = None