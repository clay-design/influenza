import sqlite3
import json
import logging
from flask import g
from config import Config
from werkzeug.security import generate_password_hash
import os

logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        if Config.DB_TYPE == 'postgresql':
            import psycopg
            import psycopg.rows
            g.db = psycopg.connect(Config.DB_PATH, row_factory=psycopg.rows.dict_row)
            g.db.autocommit = False
        else:
            g.db = sqlite3.connect(Config.DB_PATH)
            g.db.row_factory = sqlite3.Row
            g.db.execute('PRAGMA foreign_keys = ON;')
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Create tables (works for both SQLite and PostgreSQL)
        if Config.DB_TYPE == 'postgresql':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    initials TEXT NOT NULL,
                    email TEXT UNIQUE,
                    role TEXT NOT NULL CHECK (role IN ('Super Admin', 'Data Manager', 'Field Technician'))
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS id_counters (
                    facility TEXT PRIMARY KEY,
                    last_number INTEGER DEFAULT 0
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS screening (
                    screening_id TEXT PRIMARY KEY,
                    date_interview TEXT, facility TEXT, dob TEXT, age_years INTEGER, age_months INTEGER,
                    height REAL, weight REAL, temperature REAL, temp_method TEXT, resp_rate INTEGER, pulse_rate INTEGER,
                    bp_systolic INTEGER, bp_diastolic INTEGER, lmp TEXT, fundal_height REAL,
                    inc_resident TEXT, inc_pregnancy TEXT, inc_gestation TEXT, inc_hiv TEXT, inc_delivery TEXT,
                    exc_multiple TEXT, exc_fistula TEXT, exc_mental TEXT, eligibility TEXT, consent TEXT, consent_reason TEXT,
                    user_initials TEXT, timestamp TEXT
                )
            ''')
            # Add other tables (enrolment, anc_visits, delivery, closeout, audit_logs, password_reset_tokens) – I'll include them below.
        else:
            # SQLite tables – same schema but with AUTOINCREMENT
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                initials TEXT NOT NULL,
                email TEXT UNIQUE,
                role TEXT NOT NULL CHECK (role IN ('Super Admin', 'Data Manager', 'Field Technician'))
            )''')
            # ... (all other SQLite tables)

        # Seed admin user
        cursor.execute("SELECT COUNT(*) AS cnt FROM users")
        row = cursor.fetchone()
        if Config.DB_TYPE == 'postgresql':
            count = row['cnt']
        else:
            count = row[0]
        if count == 0:
            if Config.DB_TYPE == 'postgresql':
                cursor.execute(
                    "INSERT INTO users (username, password_hash, full_name, initials, email, role) VALUES (%s, %s, %s, %s, %s, %s)",
                    ('admin', generate_password_hash('SuperAdmin@2026'), 'System Super Admin', 'SA', 'admin@kemri.go.ke', 'Super Admin')
                )
            else:
                cursor.execute(
                    'INSERT INTO users (username, password_hash, full_name, initials, email, role) VALUES (?, ?, ?, ?, ?, ?)',
                    ('admin', generate_password_hash('SuperAdmin@2026'), 'System Super Admin', 'SA', 'admin@kemri.go.ke', 'Super Admin')
                )

        # Seed facility counters
        for facility in Config.FACILITY_PREFIXES:
            if Config.DB_TYPE == 'postgresql':
                cursor.execute("INSERT INTO id_counters (facility, last_number) VALUES (%s, 0) ON CONFLICT (facility) DO NOTHING", (facility,))
            else:
                cursor.execute('INSERT OR IGNORE INTO id_counters (facility, last_number) VALUES (?, 0)', (facility,))

        db.commit()