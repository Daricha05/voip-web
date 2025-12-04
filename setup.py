from setuptools import setup, find_packages
from pathlib import Path

# Lire le README pour la description longue
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Lire les requirements
requirements = []
with open('requirements.txt') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            # Séparer les dépendances optionnelles
            if 'optional' not in line.lower():
                requirements.append(line)

setup(
    name="voip-web",
    version="1.0.0",
    author="ANDRIAMANALINA Johnny Richard",
    author_email="johnnyricharde5@gmail.com",
    description="Serveur VoIP web avec Flask-SocketIO et WebRTC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Daricha05/voip-web.git",
    project_urls={
        "Bug Tracker": "https://github.com/Daricha05/voip-web/issues",
        "Documentation": "https://voip-web.readthedocs.io",
        "Source Code": "https://github.com/Daricha05/voip-web",
    },
    packages=find_packages(exclude=['tests', 'tests.*']),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Chat",
        "Topic :: Communications :: Conferencing",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Flask",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        'redis': ['redis>=4.5.0'],
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'pytest-flask>=1.2.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.4.0',
        ],
        'docs': [
            'sphinx>=7.0.0',
            'sphinx-rtd-theme>=1.2.0',
        ],
    },
    include_package_data=True,
    package_data={
        "voip_web": [
            "templates/*.html",
            "static/*",
            "static/**/*",
        ],
    },
    entry_points={
        "console_scripts": [
            "voip-web=voip_web.cli:cli",
        ],
    },
    keywords=[
        'voip', 'webrtc', 'flask', 'socketio', 'chat', 
        'video-call', 'audio-call', 'real-time', 'websocket'
    ],
    zip_safe=False,
)