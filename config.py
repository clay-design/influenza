import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    PERMANENT_SESSION_LIFETIME = 20 * 60
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1')
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

    DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')

    DB_PATH = os.environ.get('DB_PATH', 'kemri_influenza_enterprise.db')

    DATABASE_URL = os.environ.get('DATABASE_URL', '')

    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'postgres')
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

    FACILITY_PREFIXES = {
        'Bondo': 'BND',
        'Siaya': 'SIA',
        'Kuoyo': 'KUO',
        'Lumumba': 'LUM'
    }