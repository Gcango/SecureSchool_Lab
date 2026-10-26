import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"

class Config:
    # Valor por omissão apenas para laboratório local. Em produção, use SECRET_KEY no ambiente.
    SECRET_KEY = os.getenv("SECRET_KEY", "secureschool-local-lab-change-me")
    DATABASE = str(DATA_DIR / "secureschool.db")
    UPLOAD_FOLDER = str(UPLOAD_DIR)
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=15)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Em localhost sem HTTPS, Secure=False. Em produção com HTTPS deve ser True.
    SESSION_COOKIE_SECURE = False
