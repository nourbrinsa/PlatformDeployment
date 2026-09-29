import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY              = os.environ.get("SECRET_KEY", "dev-change-me")
   # SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///dev.db"    # fallback so app doesn't crash without .env
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USE_MOCK_WORKER_AGENT   = os.environ.get("USE_MOCK_WORKER_AGENT", "true").lower() == "true"
