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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enrolment (
                    screening_id TEXT PRIMARY KEY, facility TEXT, dob TEXT, age_years INTEGER, age_months INTEGER,
                    marital_status TEXT, husband_name TEXT, village TEXT, education TEXT, occupation TEXT, occupation_other TEXT,
                    height REAL, weight REAL, temperature REAL, temp_method TEXT, resp_rate INTEGER, pulse_rate INTEGER,
                    bp_systolic INTEGER, bp_diastolic INTEGER, estimated_ga_us REAL, user_initials TEXT, timestamp TEXT,
                    FOREIGN KEY (screening_id) REFERENCES screening(screening_id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS anc_visits (
                    id SERIAL PRIMARY KEY, 
                    screening_id TEXT, facility TEXT, dob TEXT, age_years INTEGER, age_months INTEGER,
                    visit_number INTEGER, visit_date TEXT, gestational_age_weeks REAL, weight REAL, 
                    bp_systolic INTEGER, bp_diastolic INTEGER, fundal_height REAL, muac REAL, 
                    complaints TEXT, medication_given TEXT, next_appointment_date TEXT, 
                    user_initials TEXT, timestamp TEXT,
                    FOREIGN KEY (screening_id) REFERENCES enrolment(screening_id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS delivery (
                    screening_id TEXT PRIMARY KEY, facility TEXT, dob TEXT, age_years INTEGER, age_months INTEGER,
                    date_interview TEXT, mother_weight REAL, vital_temp REAL, vital_temp_method TEXT,
                    vital_rr INTEGER, vital_hr INTEGER, bp_systolic INTEGER, bp_diastolic INTEGER, oxygen_sat INTEGER, oxygen_supp TEXT,
                    bmi_calc REAL, abnormal_exam TEXT, abnormal_specify TEXT, delivery_date TEXT, delivery_time TEXT, delivery_location TEXT,
                    delivery_location_other TEXT, delivery_provider TEXT, delivery_provider_other TEXT, mode_delivery TEXT,
                    csection_indication TEXT, csection_indication_other TEXT, birth_weight_g REAL, infant_sex TEXT, infant_status TEXT,
                    birth_asphyxia TEXT, user_initials TEXT, timestamp TEXT,
                    FOREIGN KEY (screening_id) REFERENCES enrolment(screening_id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS closeout (
                    screening_id TEXT PRIMARY KEY, facility TEXT, dob TEXT, age_years INTEGER, age_months INTEGER,
                    date_interview TEXT, termination_date TEXT, participant_status TEXT,
                    discontinuation_reason TEXT, discontinuation_specify TEXT, user_initials TEXT, timestamp TEXT,
                    FOREIGN KEY (screening_id) REFERENCES screening(screening_id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY, table_name TEXT, record_id TEXT, action TEXT,
                    old_value TEXT, new_value TEXT, change_reason TEXT, user_initials TEXT, timestamp TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    token TEXT NOT NULL,
                    expiry TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
        else:
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                initials TEXT NOT NULL,
                email TEXT UNIQUE,
                role TEXT NOT NULL CHECK (role IN ('Super Admin', 'Data Manager', 'Field Technician'))
            )''')
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN email TEXT UNIQUE')
            except sqlite3.OperationalError:
                pass

            cursor.execute('''CREATE TABLE IF NOT EXISTS id_counters (
                facility TEXT PRIMARY KEY,
                last_number INTEGER DEFAULT 0
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS screening (
                screening_id TEXT PRIMARY KEY,
                date_interview TEXT, facility TEXT, dob TEXT, age_years INTEGER, age_months INTEGER,
                height REAL, weight REAL, temperature REAL, temp_method TEXT, resp_rate INTEGER, pulse_rate INTEGER,
                bp_systolic INTEGER, bp_diastolic INTEGER, lmp TEXT, fundal_height REAL,
                inc_resident TEXT, inc_pregnancy TEXT, inc_gestation TEXT, inc_hiv TEXT, inc_delivery TEXT,
                exc_multiple TEXT, exc_fistula TEXT, exc_mental TEXT, eligibility TEXT, consent TEXT, consent_reason TEXT,
                user_initials TEXT, timestamp TEXT
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS enrolment (
                screening_id TEXT PRIMARY KEY, facility TEXT, dob TEXT, age_years INTEGER, age_months INTEGER,
                marital_status TEXT, husband_name TEXT, village TEXT, education TEXT, occupation TEXT, occupation_other TEXT,
                height REAL, weight REAL, temperature REAL, temp_method TEXT, resp_rate INTEGER, pulse_rate INTEGER,
                bp_systolic INTEGER, bp_diastolic INTEGER, estimated_ga_us REAL, user_initials TEXT, timestamp TEXT,
                FOREIGN KEY (screening_id) REFERENCES screening(screening_id) ON DELETE CASCADE
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS anc_visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                screening_id TEXT, facility TEXT, dob TEXT, age_years INTEGER, age_months INTEGER,
                visit_number INTEGER, visit_date TEXT, gestational_age_weeks REAL, weight REAL, 
                bp_systolic INTEGER, bp_diastolic INTEGER, fundal_height REAL, muac REAL, 
                complaints TEXT, medication_given TEXT, next_appointment_date TEXT, 
                user_initials TEXT, timestamp TEXT,
                FOREIGN KEY (screening_id) REFERENCES enrolment(screening_id) ON DELETE CASCADE
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS delivery (
                screening_id TEXT PRIMARY KEY, facility TEXT, dob TEXT, age_years INTEGER, age_months INTEGER,
                date_interview TEXT, mother_weight REAL, vital_temp REAL, vital_temp_method TEXT,
                vital_rr INTEGER, vital_hr INTEGER, bp_systolic INTEGER, bp_diastolic INTEGER, oxygen_sat INTEGER, oxygen_supp TEXT,
                bmi_calc REAL, abnormal_exam TEXT, abnormal_specify TEXT, delivery_date TEXT, delivery_time TEXT, delivery_location TEXT,
                delivery_location_other TEXT, delivery_provider TEXT, delivery_provider_other TEXT, mode_delivery TEXT,
                csection_indication TEXT, csection_indication_other TEXT, birth_weight_g REAL, infant_sex TEXT, infant_status TEXT,
                birth_asphyxia TEXT, user_initials TEXT, timestamp TEXT,
                FOREIGN KEY (screening_id) REFERENCES enrolment(screening_id) ON DELETE CASCADE
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS closeout (
                screening_id TEXT PRIMARY KEY, facility TEXT, dob TEXT, age_years INTEGER, age_months INTEGER,
                date_interview TEXT, termination_date TEXT, participant_status TEXT,
                discontinuation_reason TEXT, discontinuation_specify TEXT, user_initials TEXT, timestamp TEXT,
                FOREIGN KEY (screening_id) REFERENCES screening(screening_id) ON DELETE CASCADE
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, table_name TEXT, record_id TEXT, action TEXT,
                old_value TEXT, new_value TEXT, change_reason TEXT, user_initials TEXT, timestamp TEXT
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL,
                expiry TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )''')

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

        for facility in Config.FACILITY_PREFIXES:
            if Config.DB_TYPE == 'postgresql':
                cursor.execute("INSERT INTO id_counters (facility, last_number) VALUES (%s, 0) ON CONFLICT (facility) DO NOTHING", (facility,))
            else:
                cursor.execute('INSERT OR IGNORE INTO id_counters (facility, last_number) VALUES (?, 0)', (facility,))

        db.commit()
    app.teardown_appcontext(close_db)