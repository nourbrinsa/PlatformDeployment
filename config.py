import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Pas de valeur par défaut : l'app refuse de démarrer sans secret (vérifié dans create_app)
    SECRET_KEY   = os.environ.get("SECRET_KEY")
    WORKER_TOKEN = os.environ.get("WORKER_TOKEN")  # jeton partagé Controller <-> Workers

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USE_MOCK_WORKER_AGENT = os.environ.get("USE_MOCK_WORKER_AGENT", "true").lower() == "true"

    # Cookies de session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE   = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"  # true en prod (HTTPS)
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 h

    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    WORKER_TOKEN = "test-worker-token"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    USE_MOCK_WORKER_AGENT = True
    WTF_CSRF_ENABLED = False
