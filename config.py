import os
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    PERMANENT_SESSION_LIFETIME = 20 * 60
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1')

    FACILITY_PREFIXES = {
        'Bondo': 'BND',
        'Siaya': 'SIA',
        'Kuoyo': 'KUO',
        'Lumumba': 'LUM'
    }

    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    if DATABASE_URL:
        DB_PATH = DATABASE_URL
        DB_TYPE = 'postgresql'
    else:
        DB_PATH = os.environ.get('DB_PATH', 'kemri_influenza_enterprise.db')
        DB_TYPE = 'sqlite'