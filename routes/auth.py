from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from models import get_db, ph          # <-- added ph import
from config import Config
import secrets
from datetime import datetime, timedelta
import traceback

auth_bp = Blueprint('auth', __name__)

def generate_initials(full_name):
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0][:2].upper()
    else:
        return (parts[0][0] + parts[-1][0]).upper()

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

@auth_bp.route('/forgot-password', methods=['GET'])
def forgot_password_page():
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET'])
def reset_password_page(token):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        f"SELECT user_id FROM password_reset_tokens WHERE token = {ph()} AND expiry > {ph()}",
        (token, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    row = cursor.fetchone()
    if not row:
        return "Invalid or expired token", 400
    return render_template('reset_password.html', token=token)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM users WHERE username = {ph()}", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session.permanent = True
            session['user'] = {
                'username': user['username'],
                'role': user['role'],
                'initials': user['initials']
            }
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        print("LOGIN ERROR:", traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        full_name = data.get('full_name')
        email = data.get('email')
        initials = generate_initials(full_name) if full_name else 'XX'

        if not all([username, password, full_name, email]):
            return jsonify({'success': False, 'message': 'All fields including email are required'}), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute(f"SELECT id FROM users WHERE username = {ph()}", (username,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Username already exists'}), 400

        cursor.execute(f"SELECT id FROM users WHERE email = {ph()}", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400

        cursor.execute(
            f"INSERT INTO users (username, password_hash, full_name, initials, email, role) VALUES ({ph()}, {ph()}, {ph()}, {ph()}, {ph()}, {ph()})",
            (username, generate_password_hash(password), full_name, initials, email, 'Field Technician')
        )
        db.commit()
        return jsonify({'success': True, 'message': 'Account created successfully. Please log in.'})
    except Exception as e:
        print("REGISTER ERROR:", traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json() or {}
        email = data.get('email')
        if not email:
            return jsonify({'success': False, 'message': 'Email address required'}), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute(f"SELECT id, username, email FROM users WHERE email = {ph()}", (email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': True, 'message': 'If the email exists, a reset link has been sent.'})

        token = secrets.token_urlsafe(32)
        expiry = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute(f"DELETE FROM password_reset_tokens WHERE user_id = {ph()}", (user['id'],))
        cursor.execute(
            f"INSERT INTO password_reset_tokens (user_id, token, expiry) VALUES ({ph()}, {ph()}, {ph()})",
            (user['id'], token, expiry)
        )
        db.commit()

        base_url = current_app.config['BASE_URL']
        reset_link = f"{base_url}/reset-password/{token}"
        print(f"\n=== PASSWORD RESET LINK for {email}: {reset_link} ===\n")

        return jsonify({'success': True, 'message': 'Password reset link generated. Check the server console for the link.'})
    except Exception as e:
        print("FORGOT PASSWORD ERROR:", traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/api/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json() or {}
        token = data.get('token')
        new_password = data.get('new_password')
        if not token or not new_password:
            return jsonify({'success': False, 'message': 'Token and password required'}), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            f"SELECT user_id FROM password_reset_tokens WHERE token = {ph()} AND expiry > {ph()}",
            (token, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 400

        cursor.execute(
            f"UPDATE users SET password_hash = {ph()} WHERE id = {ph()}",
            (generate_password_hash(new_password), row['user_id'])
        )
        cursor.execute(f"DELETE FROM password_reset_tokens WHERE token = {ph()}", (token,))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        print("RESET PASSWORD ERROR:", traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/api/verify-password', methods=['POST'])
def verify_password():
    try:
        data = request.get_json() or {}
        password = data.get('password')
        if not password:
            return jsonify({'success': False, 'message': 'Password required'}), 400

        if 'user' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401

        username = session['user']['username']
        db = get_db()
        cursor = db.cursor()
        cursor.execute(f"SELECT password_hash FROM users WHERE username = {ph()}", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password_hash'], password):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Incorrect password'}), 401
    except Exception as e:
        print("VERIFY PASSWORD ERROR:", traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@auth_bp.before_app_request
def enforce_login():
    allowed = (
        'auth.login_page', 'auth.login', 'auth.register_page', 'auth.register',
        'auth.forgot_password_page', 'auth.forgot_password',
        'auth.reset_password_page', 'auth.reset_password', 'static'
    )
    if request.endpoint in allowed:
        return
    if 'user' not in session:
        return redirect(url_for('auth.login_page'))