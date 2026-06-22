from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from models import get_db
from config import Config
import sqlite3

admin_bp = Blueprint('admin', __name__)

def ph():
    return '%s' if Config.DB_TYPE == 'postgresql' else '?'

@admin_bp.route('/users/add', methods=['POST'])
def add_user():
    if session.get('user', {}).get('role') != 'Super Admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    data = request.get_json() or {}
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            f"INSERT INTO users (username, password_hash, full_name, initials, email, role) VALUES ({ph()}, {ph()}, {ph()}, {ph()}, {ph()}, {ph()})",
            (data.get('username'), generate_password_hash(data.get('password')),
             data.get('full_name'), data.get('initials'), data.get('email'), data.get('role'))
        )
        db.commit()
        return jsonify({'success': True, 'message': 'User created successfully.'})
    except Exception as e:
        if 'username' in str(e) or 'UNIQUE' in str(e):
            return jsonify({'success': False, 'message': 'Username or email already exists'}), 400
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/users/list', methods=['GET'])
def list_users():
    if session.get('user', {}).get('role') != 'Super Admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, full_name, initials, email, role FROM users ORDER BY username")
    users = cursor.fetchall()
    return jsonify([dict(u) for u in users])

@admin_bp.route('/admin/reset-password', methods=['POST'])
def admin_reset_password():
    if session.get('user', {}).get('role') != 'Super Admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    data = request.get_json() or {}
    user_id = data.get('user_id')
    new_password = data.get('new_password')

    if not user_id or not new_password:
        return jsonify({'success': False, 'message': 'User ID and password required'}), 400

    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT id FROM users WHERE id = {ph()}", (user_id,))
    if not cursor.fetchone():
        return jsonify({'success': False, 'message': 'User not found'}), 404

    cursor.execute(
        f"UPDATE users SET password_hash = {ph()} WHERE id = {ph()}",
        (generate_password_hash(new_password), user_id)
    )
    db.commit()
    return jsonify({'success': True, 'message': 'Password reset successfully.'})

@admin_bp.route('/audit/history/<screening_id>')
def audit_history(screening_id):
    user_role = session.get('user', {}).get('role')
    if user_role not in ['Super Admin', 'Data Manager']:
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        f"SELECT * FROM audit_logs WHERE record_id = {ph()} ORDER BY timestamp DESC",
        (screening_id,)
    )
    rows = cursor.fetchall()
    return jsonify([dict(r) for r in rows])

@admin_bp.route('/generate_id', methods=['GET'])
def generate_id():
    facility = request.args.get('facility')
    prefix = Config.FACILITY_PREFIXES.get(facility)
    if not prefix:
        return jsonify({'success': False, 'message': 'Invalid facility'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT last_number FROM id_counters WHERE facility = {ph()}", (facility,))
    row = cursor.fetchone()
    next_serial = (row['last_number'] if row else 0) + 1
    generated_id = f"{prefix}-2026-{next_serial:04d}"
    return jsonify({'success': True, 'screening_id': generated_id})

@admin_bp.route('/lookup/screening/<screening_id>', methods=['GET'])
def lookup_screening(screening_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM screening WHERE screening_id = {ph()}", (screening_id,))
    row = cursor.fetchone()
    if row:
        return jsonify({'success': True, 'data': dict(row)})
    return jsonify({'success': False, 'message': 'Not found'}), 404

@admin_bp.route('/fetch/enrolment/<screening_id>')
def fetch_enrolment(screening_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM enrolment WHERE screening_id = {ph()}", (screening_id,))
    row = cursor.fetchone()
    return jsonify({'success': True, 'data': dict(row) if row else None})

@admin_bp.route('/fetch/anc/<screening_id>')
def fetch_anc(screening_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        f"SELECT * FROM anc_visits WHERE screening_id = {ph()} ORDER BY visit_number",
        (screening_id,)
    )
    rows = cursor.fetchall()
    return jsonify({'success': True, 'data': [dict(r) for r in rows]})

@admin_bp.route('/fetch/delivery/<screening_id>')
def fetch_delivery(screening_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM delivery WHERE screening_id = {ph()}", (screening_id,))
    row = cursor.fetchone()
    return jsonify({'success': True, 'data': dict(row) if row else None})

@admin_bp.route('/fetch/closeout/<screening_id>')
def fetch_closeout(screening_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM closeout WHERE screening_id = {ph()}", (screening_id,))
    row = cursor.fetchone()
    return jsonify({'success': True, 'data': dict(row) if row else None})