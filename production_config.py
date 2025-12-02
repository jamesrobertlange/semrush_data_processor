"""
Production Configuration
"""
import os
import secrets
from dataclasses import dataclass


@dataclass
class ProductionConfig:
    # Security
    SECRET_KEY: str = os.getenv('SECRET_KEY', secrets.token_hex(32))
    
    # File handling
    MAX_FILE_SIZE_MB: int = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
    MAX_WORKERS: int = int(os.getenv('MAX_WORKERS', '2'))
    PREVIEW_ROWS: int = 10
    
    # Upload settings
    UPLOAD_FOLDER: str = '/tmp/semrush_uploads'
    ALLOWED_EXTENSIONS: set = {'csv'}
    
    # Session settings
    SESSION_COOKIE_SECURE: bool = True  # Enable when using HTTPS
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    
    # Cleanup settings
    TEMP_FILE_MAX_AGE_HOURS: int = 24


production_config = ProductionConfig()
