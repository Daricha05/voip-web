import click
import sys
import os
from pathlib import Path

from .config import Config, get_config, reload_config
from .utils import get_local_ip


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """VoIP Web Server - Serveur de chat vocal et vidéo"""
    pass


@cli.command()
@click.option('--host', default=None, help='Adresse IP du serveur')
@click.option('--port', default=None, type=int, help='Port du serveur')
@click.option('--config', default=None, help='Fichier de configuration YAML')
@click.option('--no-ssl', is_flag=True, help='Désactiver SSL')
@click.option('--debug', is_flag=True, help='Mode debug')
def start(host, port, config, no_ssl, debug):
    """Démarre le serveur VoIP"""
    
    # Charger la configuration
    if config:
        cfg = Config(config)
    else:
        # Chercher config.yml dans le répertoire courant
        default_config = Path('config.yml')
        if default_config.exists():
            cfg = Config('config.yml')
        else:
            cfg = Config()
    
    # Surcharger avec les options CLI
    if host:
        cfg.set('server', 'host', value=host)
    if port:
        cfg.set('server', 'port', value=port)
    if no_ssl:
        cfg.set('ssl', 'enabled', value=False)
    if debug:
        cfg.set('server', 'debug', value=True)
    
    # Importer ici pour éviter les imports circulaires
    from .server import create_app, create_socketio
    import eventlet
    import eventlet.wsgi
    
    # Créer l'app
    app = create_app(cfg.to_dict())
    socketio = create_socketio(
        app,
        cors_allowed_origins=cfg.get('socketio', 'cors_allowed_origins'),
        ping_timeout=cfg.get('socketio', 'ping_timeout'),
        ping_interval=cfg.get('socketio', 'ping_interval')
    )
    
    # Enregistrer les handlers SocketIO
    from .server import register_socketio_handlers
    register_socketio_handlers(socketio)
    
    # Afficher les informations
    server_host = cfg.get('server', 'host')
    server_port = cfg.get('server', 'port')
    ssl_enabled = cfg.get('ssl', 'enabled')
    server_ip = get_local_ip()
    
    protocol = 'https' if ssl_enabled else 'http'
    
    click.echo("\n" + "="*60)
    click.echo(click.style("SERVEUR WEB VOIP DÉMARRÉ", fg='green', bold=True))
    click.echo("="*60)
    click.echo(f"IP: {server_ip}")
    click.echo(f"Port: {server_port}")
    click.echo(f"URL locale: {protocol}://{server_ip}:{server_port}")
    click.echo(f"URL chat: {protocol}://{server_ip}:{server_port}/chat")
    click.echo(f"SSL: {'Activé' if ssl_enabled else 'Désactivé'}")
    click.echo(f"Stockage: {'Redis' if cfg.get('redis', 'enabled') else 'Mémoire'}")
    click.echo("="*60)
    click.echo("Scannez le QR code sur la page d'accueil !")
    click.echo("="*60 + "\n")
    
    # Démarrer le serveur
    try:
        if ssl_enabled:
            cert_file = cfg.get('ssl', 'cert_file')
            key_file = cfg.get('ssl', 'key_file')
            
            if not Path(cert_file).exists() or not Path(key_file).exists():
                click.echo(click.style(f"✗ Certificats SSL introuvables: {cert_file}, {key_file}", fg='red'))
                click.echo("Générez-les avec: voip-web generate-certs")
                sys.exit(1)
            
            context = eventlet.wrap_ssl(
                eventlet.listen((server_host, server_port)),
                certfile=cert_file,
                keyfile=key_file,
                server_side=True
            )
            eventlet.wsgi.server(context, app)
        else:
            socketio.run(
                app,
                host=server_host,
                port=server_port,
                debug=cfg.get('server', 'debug')
            )
    except KeyboardInterrupt:
        click.echo("\n✓ Serveur arrêté")
    except Exception as e:
        click.echo(click.style(f"✗ Erreur: {e}", fg='red'))
        sys.exit(1)


@cli.command()
@click.option('--output', default='config.yml', help='Fichier de sortie')
def init_config(output):
    """Génère un fichier de configuration par défaut"""
    
    cfg = Config()
    cfg.save_to_file(output)
    
    click.echo(click.style(f"✓ Configuration générée: {output}", fg='green'))
    click.echo("\nÉditez ce fichier pour personnaliser votre serveur.")


@cli.command()
def generate_certs():
    """Génère des certificats SSL auto-signés pour le développement"""
    
    try:
        import subprocess
        
        click.echo("Génération des certificats SSL...")
        
        # Générer la clé privée et le certificat
        result = subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
            '-keyout', 'key.pem', '-out', 'cert.pem',
            '-days', '365', '-nodes',
            '-subj', '/CN=localhost'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            click.echo(click.style("✓ Certificats générés avec succès!", fg='green'))
            click.echo("  - cert.pem")
            click.echo("  - key.pem")
            click.echo("\nCes certificats sont pour le développement uniquement.")
        else:
            click.echo(click.style("✗ Erreur lors de la génération", fg='red'))
            click.echo(result.stderr)
            
    except FileNotFoundError:
        click.echo(click.style("✗ OpenSSL n'est pas installé", fg='red'))
        click.echo("Installez OpenSSL pour générer les certificats.")


@cli.command()
@click.option('--config', default='config.yml', help='Fichier de configuration')
def show_config(config):
    """Affiche la configuration actuelle"""
    
    if Path(config).exists():
        cfg = Config(config)
    else:
        cfg = Config()
        click.echo(click.style(f"{config} non trouvé, affichage de la config par défaut\n", fg='yellow'))
    
    import yaml
    click.echo(yaml.dump(cfg.to_dict(), default_flow_style=False))


@cli.command()
def test():
    """Teste la configuration et les dépendances"""
    
    click.echo("Test de la configuration...\n")
    
    # Test des imports
    errors = []
    
    click.echo("Vérification des dépendances:")
    packages = {
        'flask': 'Flask',
        'flask_socketio': 'Flask-SocketIO',
        'eventlet': 'Eventlet',
        'qrcode': 'qrcode',
        'yaml': 'PyYAML'
    }
    
    for module, name in packages.items():
        try:
            __import__(module)
            click.echo(f"  ✓ {name}")
        except ImportError:
            click.echo(click.style(f"  ✗ {name} manquant", fg='red'))
            errors.append(name)
    
    # Test Redis (optionnel)
    try:
        import redis
        click.echo(f"  ✓ redis (optionnel)")
    except ImportError:
        click.echo(f" redis non installé (optionnel)")
    
    # Test de la configuration
    click.echo("\n Configuration:")
    cfg = Config()
    
    ssl_enabled = cfg.get('ssl', 'enabled')
    if ssl_enabled:
        cert_exists = Path(cfg.get('ssl', 'cert_file')).exists()
        key_exists = Path(cfg.get('ssl', 'key_file')).exists()
        
        if cert_exists and key_exists:
            click.echo("  ✓ Certificats SSL présents")
        else:
            click.echo(click.style("  ✗ Certificats SSL manquants", fg='red'))
            click.echo("    Générez-les avec: voip-web generate-certs")
            errors.append("SSL")
    
    # Résumé
    click.echo("\n" + "="*50)
    if errors:
        click.echo(click.style(f"✗ {len(errors)} problème(s) détecté(s)", fg='red'))
        click.echo(f"Packages manquants: {', '.join(errors)}")
    else:
        click.echo(click.style("✓ Tous les tests sont OK!", fg='green'))
    click.echo("="*50)


@cli.command()
def info():
    """Affiche les informations du serveur"""
    
    server_ip = get_local_ip()
    
    click.echo("\n" + "="*50)
    click.echo(click.style("Informations VoIP Web Server", fg='cyan', bold=True))
    click.echo("="*50)
    click.echo(f"Version: 1.0.0")
    click.echo(f"IP locale: {server_ip}")
    click.echo(f"Hostname: {os.uname().nodename}")
    click.echo("="*50 + "\n")


if __name__ == '__main__':
    cli()