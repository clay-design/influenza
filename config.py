import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    PERMANENT_SESSION_LIFETIME = 20 * 60
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1')
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

    # Simple SQLite – works on Render with /tmp/
    DB_PATH = os.environ.get('DB_PATH', 'kemri_influenza_enterprise.db')
    DB_TYPE = 'sqlite3'

    FACILITY_PREFIXES = {
        'Bondo': 'BND',
        'Siaya': 'SIA',
        'Kuoyo': 'KUO',
        'Lumumba': 'LUM'
    }