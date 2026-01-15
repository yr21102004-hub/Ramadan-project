import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Base Configuration Class.
    Follows Clean Code principles by separating concern of configuration from application logic.
    """
    SECRET_KEY = os.getenv('SECRET_KEY', 'simple_secret_key')
    SESSION_COOKIE_SECURE = False # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate Limiting
    RATELIMIT_DEFAULT = "200 per day"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Database
    DATABASE_PATH = 'ramadan_company.db'
    BACKUP_DIR = 'backups'
    
    # File Uploads
    UPLOAD_FOLDER = os.path.join('static', 'user_images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB Max
