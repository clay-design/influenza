import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    PERMANENT_SESSION_LIFETIME = 20 * 60
    DB_PATH = os.environ.get('DB_PATH', 'kemri_influenza_enterprise.db')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')

    FACILITY_PREFIXES = {
        'Bondo': 'BND',
        'Siaya': 'SIA',
        'Kuoyo': 'KUO',
        'Lumumba': 'LUM'
    }

    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')