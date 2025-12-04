from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="voip-web",
    version="1.0.0",
    author="ANDRIAMANALINA Johnny Richard",
    author_email="johnnyricharde5@gmail.com",
    description="Serveur VoIP web avec Flask-SocketIO et WebRTC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Daricha05/voip-web.git",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: Flask",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Flask>=2.3.0",
        "flask-socketio>=5.3.0",
        "python-socketio>=5.9.0",
        "qrcode[pil]>=7.4.0",
        "eventlet>=0.33.0",
    ],
    include_package_data=True,
    package_data={
        "voip_web": [
            "templates/*.html",
            "static/*",
        ],
    },
    entry_points={
        "console_scripts": [
            "voip-web=voip_web.server:main",
        ],
    },
)
