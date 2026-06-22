from flask import Blueprint, render_template, session, abort, request, jsonify
from models import get_db

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def dashboard():
    return render_template('dashboard.html')

@views_bp.route('/data')
def data_view():
    if session.get('user', {}).get('role') != 'Super Admin':
        abort(403)
    return render_template('data.html')

@views_bp.route('/form/screening')
def screening():
    return render_template('screening.html')

@views_bp.route('/form/enrolment')
def enrolment():
    return render_template('enrolment.html')

@views_bp.route('/form/anc')
def anc():
    return render_template('anc.html')

@views_bp.route('/form/delivery')
def delivery():
    return render_template('delivery.html')

@views_bp.route('/form/closeout')
def closeout():
    return render_template('closeout.html')

@views_bp.route('/users')
def users():
    if session.get('user', {}).get('role') != 'Super Admin':
        abort(403)
    return render_template('users.html')

@views_bp.route('/api/search', methods=['GET'])
def search_participants():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    db = get_db()
    rows = db.execute(
        '''SELECT screening_id, facility, dob, age_years, age_months, eligibility, consent,
                  user_initials, timestamp
           FROM screening
           WHERE screening_id LIKE ? OR facility LIKE ? OR dob LIKE ?
           ORDER BY timestamp DESC
           LIMIT 50''',
        (f'%{q}%', f'%{q}%', f'%{q}%')
    ).fetchall()
    return jsonify([dict(r) for r in rows])