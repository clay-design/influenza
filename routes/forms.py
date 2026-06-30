import json
import logging
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from models import get_db, ph         
from config import Config

forms_bp = Blueprint('forms', __name__)
logger = logging.getLogger(__name__)

def audit_log(table, record_id, action, old_value, new_value, change_reason, user_initials):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        f"INSERT INTO audit_logs (table_name, record_id, action, old_value, new_value, change_reason, user_initials, timestamp) VALUES ({ph()}, {ph()}, {ph()}, {ph()}, {ph()}, {ph()}, {ph()}, {ph()})",
        (table, record_id, action,
         json.dumps(dict(old_value)) if old_value else None,
         json.dumps(new_value) if new_value else None,
         change_reason or 'Form Submission',
         user_initials,
         datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    db.commit()

def validate_positive_number(value, field_name):
    if value is not None and isinstance(value, (int, float)) and value < 0:
        raise ValueError(f"{field_name} cannot be negative")

@forms_bp.route('/calculate_ga', methods=['POST'])
def calculate_ga():
    data = request.get_json() or {}
    lmp = data.get('lmp')
    if not lmp:
        return jsonify({'success': False, 'message': 'LMP date required'}), 400
    try:
        from datetime import datetime
        lmp_date = datetime.strptime(lmp, '%Y-%m-%d')
        today = datetime.today()
        delta = today - lmp_date
        weeks = delta.days / 7
        return jsonify({'success': True, 'ga_weeks': round(weeks, 1)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@forms_bp.route('/audit/<screening_id>', methods=['GET'])
def get_audit_logs(screening_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        f"SELECT * FROM audit_logs WHERE record_id = {ph()} ORDER BY timestamp DESC",
        (screening_id,)
    )
    rows = cursor.fetchall()
    return jsonify([dict(r) for r in rows])

@forms_bp.route('/submit/screening', methods=['POST'])
def submit_screening():
    if session['user']['role'] == 'Field Technician':
        return jsonify({'success': False, 'message': 'Write access restricted'}), 403

    data = request.get_json() or {}
    sid = data.get('screening_id')
    facility = data.get('facility')
    if not sid or not facility:
        return jsonify({'success': False, 'message': 'Missing screening_id or facility'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM screening WHERE screening_id = {ph()}", (sid,))
    old = cursor.fetchone()
    action = 'UPDATE' if old else 'CREATE'

    try:
        validate_positive_number(float(data.get('height', 0)), 'Height')
        validate_positive_number(float(data.get('weight', 0)), 'Weight')
        validate_positive_number(float(data.get('temperature', 0)), 'Temperature')
        validate_positive_number(int(data.get('resp_rate', 0)), 'Respiratory Rate')
        validate_positive_number(int(data.get('pulse_rate', 0)), 'Pulse Rate')
        validate_positive_number(int(data.get('bp_systolic', 0)), 'BP Systolic')
        validate_positive_number(int(data.get('bp_diastolic', 0)), 'BP Diastolic')
        validate_positive_number(float(data.get('fundal_height', 0)), 'Fundal Height')
    except ValueError as ve:
        return jsonify({'success': False, 'message': str(ve)}), 400

    if action == 'UPDATE' and not data.get('change_reason'):
        return jsonify({'success': False, 'message': 'Change reason is required when editing'}), 400

    try:
        if action == 'CREATE':
            cursor.execute(f"UPDATE id_counters SET last_number = last_number + 1 WHERE facility = {ph()}", (facility,))
            cursor.execute(
                f"""INSERT INTO screening
                   (screening_id, date_interview, facility, dob, age_years, age_months,
                    height, weight, temperature, temp_method, resp_rate, pulse_rate,
                    bp_systolic, bp_diastolic, lmp, fundal_height,
                    inc_resident, inc_pregnancy, inc_gestation, inc_hiv, inc_delivery,
                    exc_multiple, exc_fistula, exc_mental,
                    eligibility, consent, consent_reason, user_initials, timestamp)
                   VALUES ({ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()})""",
                (
                    sid,
                    data.get('date_interview'),
                    facility,
                    data.get('dob'),
                    int(data.get('age_years', 0)),
                    int(data.get('age_months', 0)),
                    float(data.get('height', 0)),
                    float(data.get('weight', 0)),
                    float(data.get('temperature', 0)),
                    data.get('temp_method'),
                    int(data.get('resp_rate', 0)),
                    int(data.get('pulse_rate', 0)),
                    int(data.get('bp_systolic', 0)),
                    int(data.get('bp_diastolic', 0)),
                    data.get('lmp'),
                    float(data.get('fundal_height', 0)),
                    data.get('inc_resident'),
                    data.get('inc_pregnancy'),
                    data.get('inc_gestation'),
                    data.get('inc_hiv'),
                    data.get('inc_delivery'),
                    data.get('exc_multiple'),
                    data.get('exc_fistula'),
                    data.get('exc_mental'),
                    data.get('eligibility'),
                    data.get('consent'),
                    data.get('consent_reason'),
                    session['user']['initials'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
        else:
            cursor.execute(
                f"""UPDATE screening SET
                    date_interview={ph()}, facility={ph()}, dob={ph()}, age_years={ph()}, age_months={ph()},
                    height={ph()}, weight={ph()}, temperature={ph()}, temp_method={ph()},
                    resp_rate={ph()}, pulse_rate={ph()}, bp_systolic={ph()}, bp_diastolic={ph()},
                    lmp={ph()}, fundal_height={ph()},
                    inc_resident={ph()}, inc_pregnancy={ph()}, inc_gestation={ph()}, inc_hiv={ph()}, inc_delivery={ph()},
                    exc_multiple={ph()}, exc_fistula={ph()}, exc_mental={ph()},
                    eligibility={ph()}, consent={ph()}, consent_reason={ph()},
                    user_initials={ph()}, timestamp={ph()}
                    WHERE screening_id={ph()}""",
                (
                    data.get('date_interview'),
                    facility,
                    data.get('dob'),
                    int(data.get('age_years', 0)),
                    int(data.get('age_months', 0)),
                    float(data.get('height', 0)),
                    float(data.get('weight', 0)),
                    float(data.get('temperature', 0)),
                    data.get('temp_method'),
                    int(data.get('resp_rate', 0)),
                    int(data.get('pulse_rate', 0)),
                    int(data.get('bp_systolic', 0)),
                    int(data.get('bp_diastolic', 0)),
                    data.get('lmp'),
                    float(data.get('fundal_height', 0)),
                    data.get('inc_resident'),
                    data.get('inc_pregnancy'),
                    data.get('inc_gestation'),
                    data.get('inc_hiv'),
                    data.get('inc_delivery'),
                    data.get('exc_multiple'),
                    data.get('exc_fistula'),
                    data.get('exc_mental'),
                    data.get('eligibility'),
                    data.get('consent'),
                    data.get('consent_reason'),
                    session['user']['initials'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    sid
                )
            )
        audit_log('screening', sid, action, old, data, data.get('change_reason'), session['user']['initials'])
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        logger.error(f"Screening error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)}), 500

@forms_bp.route('/submit/enrolment', methods=['POST'])
def submit_enrolment():
    if session['user']['role'] == 'Field Technician':
        return jsonify({'success': False, 'message': 'Write access restricted'}), 403

    data = request.get_json() or {}
    sid = data.get('screening_id')
    if not sid:
        return jsonify({'success': False, 'message': 'Missing screening_id'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM enrolment WHERE screening_id = {ph()}", (sid,))
    old = cursor.fetchone()
    action = 'UPDATE' if old else 'CREATE'

    try:
        validate_positive_number(float(data.get('height', 0)), 'Height')
        validate_positive_number(float(data.get('weight', 0)), 'Weight')
        validate_positive_number(float(data.get('temperature', 0)), 'Temperature')
        validate_positive_number(int(data.get('resp_rate', 0)), 'Respiratory Rate')
        validate_positive_number(int(data.get('pulse_rate', 0)), 'Pulse Rate')
        validate_positive_number(int(data.get('bp_systolic', 0)), 'BP Systolic')
        validate_positive_number(int(data.get('bp_diastolic', 0)), 'BP Diastolic')
        validate_positive_number(float(data.get('estimated_ga_us', 0)), 'Estimated GA')
    except ValueError as ve:
        return jsonify({'success': False, 'message': str(ve)}), 400

    if action == 'UPDATE' and not data.get('change_reason'):
        return jsonify({'success': False, 'message': 'Change reason is required when editing'}), 400

    try:
        if action == 'CREATE':
            cursor.execute(
                f"""INSERT INTO enrolment
                   (screening_id, facility, dob, age_years, age_months,
                    marital_status, husband_name, village, education, occupation, occupation_other,
                    height, weight, temperature, temp_method, resp_rate, pulse_rate,
                    bp_systolic, bp_diastolic, estimated_ga_us, user_initials, timestamp)
                   VALUES ({ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()})""",
                (
                    sid,
                    data.get('facility'),
                    data.get('dob'),
                    int(data.get('age_years', 0)),
                    int(data.get('age_months', 0)),
                    data.get('marital_status'),
                    data.get('husband_name'),
                    data.get('village'),
                    data.get('education'),
                    data.get('occupation'),
                    data.get('occupation_other'),
                    float(data.get('height', 0)),
                    float(data.get('weight', 0)),
                    float(data.get('temperature', 0)),
                    data.get('temp_method'),
                    int(data.get('resp_rate', 0)),
                    int(data.get('pulse_rate', 0)),
                    int(data.get('bp_systolic', 0)),
                    int(data.get('bp_diastolic', 0)),
                    float(data.get('estimated_ga_us', 0)),
                    session['user']['initials'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
        else:
            cursor.execute(
                f"""UPDATE enrolment SET
                    facility={ph()}, dob={ph()}, age_years={ph()}, age_months={ph()},
                    marital_status={ph()}, husband_name={ph()}, village={ph()}, education={ph()},
                    occupation={ph()}, occupation_other={ph()},
                    height={ph()}, weight={ph()}, temperature={ph()}, temp_method={ph()},
                    resp_rate={ph()}, pulse_rate={ph()}, bp_systolic={ph()}, bp_diastolic={ph()},
                    estimated_ga_us={ph()}, user_initials={ph()}, timestamp={ph()}
                    WHERE screening_id={ph()}""",
                (
                    data.get('facility'),
                    data.get('dob'),
                    int(data.get('age_years', 0)),
                    int(data.get('age_months', 0)),
                    data.get('marital_status'),
                    data.get('husband_name'),
                    data.get('village'),
                    data.get('education'),
                    data.get('occupation'),
                    data.get('occupation_other'),
                    float(data.get('height', 0)),
                    float(data.get('weight', 0)),
                    float(data.get('temperature', 0)),
                    data.get('temp_method'),
                    int(data.get('resp_rate', 0)),
                    int(data.get('pulse_rate', 0)),
                    int(data.get('bp_systolic', 0)),
                    int(data.get('bp_diastolic', 0)),
                    float(data.get('estimated_ga_us', 0)),
                    session['user']['initials'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    sid
                )
            )
        audit_log('enrolment', sid, action, old, data, data.get('change_reason'), session['user']['initials'])
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        logger.error(f"Enrolment error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)}), 500

@forms_bp.route('/submit/anc', methods=['POST'])
def submit_anc():
    if session['user']['role'] == 'Field Technician':
        return jsonify({'success': False, 'message': 'Write access restricted'}), 403

    data = request.get_json() or {}
    sid = data.get('screening_id')
    vid = data.get('id')
    if not sid:
        return jsonify({'success': False, 'message': 'Missing screening_id'}), 400

    db = get_db()
    cursor = db.cursor()
    old = None
    action = 'CREATE'
    if vid:
        cursor.execute(f"SELECT * FROM anc_visits WHERE id = {ph()}", (vid,))
        old = cursor.fetchone()
        if old:
            action = 'UPDATE'

    try:
        validate_positive_number(float(data.get('gestational_age_weeks', 0)), 'Gestational Age')
        validate_positive_number(float(data.get('weight', 0)), 'Weight')
        validate_positive_number(int(data.get('bp_systolic', 0)), 'BP Systolic')
        validate_positive_number(int(data.get('bp_diastolic', 0)), 'BP Diastolic')
        validate_positive_number(float(data.get('fundal_height', 0)), 'Fundal Height')
        validate_positive_number(float(data.get('muac', 0)), 'MUAC')
    except ValueError as ve:
        return jsonify({'success': False, 'message': str(ve)}), 400

    if action == 'UPDATE' and not data.get('change_reason'):
        return jsonify({'success': False, 'message': 'Change reason is required when editing'}), 400

    try:
        if action == 'CREATE':
            if Config.DB_TYPE == 'postgresql':
                cursor.execute(
                    f"""INSERT INTO anc_visits
                       (screening_id, facility, dob, age_years, age_months,
                        visit_number, visit_date, gestational_age_weeks, weight,
                        bp_systolic, bp_diastolic, fundal_height, muac,
                        complaints, medication_given, next_appointment_date,
                        user_initials, timestamp)
                       VALUES ({ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()})
                       RETURNING id""",
                    (
                        sid,
                        data.get('facility'),
                        data.get('dob'),
                        int(data.get('age_years', 0)),
                        int(data.get('age_months', 0)),
                        int(data.get('visit_number')),
                        data.get('visit_date'),
                        float(data.get('gestational_age_weeks', 0)),
                        float(data.get('weight', 0)),
                        int(data.get('bp_systolic', 0)),
                        int(data.get('bp_diastolic', 0)),
                        float(data.get('fundal_height', 0)),
                        float(data.get('muac', 0)),
                        data.get('complaints'),
                        data.get('medication_given'),
                        data.get('next_appointment_date'),
                        session['user']['initials'],
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    )
                )
                row = cursor.fetchone()
                vid = row['id'] if row else None
            else:
                cursor.execute(
                    f"""INSERT INTO anc_visits
                       (screening_id, facility, dob, age_years, age_months,
                        visit_number, visit_date, gestational_age_weeks, weight,
                        bp_systolic, bp_diastolic, fundal_height, muac,
                        complaints, medication_given, next_appointment_date,
                        user_initials, timestamp)
                       VALUES ({ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()})""",
                    (
                        sid,
                        data.get('facility'),
                        data.get('dob'),
                        int(data.get('age_years', 0)),
                        int(data.get('age_months', 0)),
                        int(data.get('visit_number')),
                        data.get('visit_date'),
                        float(data.get('gestational_age_weeks', 0)),
                        float(data.get('weight', 0)),
                        int(data.get('bp_systolic', 0)),
                        int(data.get('bp_diastolic', 0)),
                        float(data.get('fundal_height', 0)),
                        float(data.get('muac', 0)),
                        data.get('complaints'),
                        data.get('medication_given'),
                        data.get('next_appointment_date'),
                        session['user']['initials'],
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    )
                )
                vid = cursor.lastrowid
        else:
            cursor.execute(
                f"""UPDATE anc_visits SET
                   screening_id={ph()}, facility={ph()}, dob={ph()}, age_years={ph()}, age_months={ph()},
                   visit_number={ph()}, visit_date={ph()}, gestational_age_weeks={ph()}, weight={ph()},
                   bp_systolic={ph()}, bp_diastolic={ph()}, fundal_height={ph()}, muac={ph()},
                   complaints={ph()}, medication_given={ph()}, next_appointment_date={ph()},
                   user_initials={ph()}, timestamp={ph()}
                   WHERE id={ph()}""",
                (
                    sid,
                    data.get('facility'),
                    data.get('dob'),
                    int(data.get('age_years', 0)),
                    int(data.get('age_months', 0)),
                    int(data.get('visit_number')),
                    data.get('visit_date'),
                    float(data.get('gestational_age_weeks', 0)),
                    float(data.get('weight', 0)),
                    int(data.get('bp_systolic', 0)),
                    int(data.get('bp_diastolic', 0)),
                    float(data.get('fundal_height', 0)),
                    float(data.get('muac', 0)),
                    data.get('complaints'),
                    data.get('medication_given'),
                    data.get('next_appointment_date'),
                    session['user']['initials'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    vid
                )
            )
        audit_log('anc_visits', str(vid), action, old, data, data.get('change_reason'), session['user']['initials'])
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        logger.error(f"ANC error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)}), 500

@forms_bp.route('/submit/delivery', methods=['POST'])
def submit_delivery():
    if session['user']['role'] == 'Field Technician':
        return jsonify({'success': False, 'message': 'Write access restricted'}), 403

    data = request.get_json() or {}
    sid = data.get('screening_id')
    if not sid:
        return jsonify({'success': False, 'message': 'Missing screening_id'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM delivery WHERE screening_id = {ph()}", (sid,))
    old = cursor.fetchone()
    action = 'UPDATE' if old else 'CREATE'

    try:
        validate_positive_number(float(data.get('mother_weight', 0)), 'Mother Weight')
        validate_positive_number(float(data.get('vital_temp', 0)), 'Temperature')
        validate_positive_number(int(data.get('vital_rr', 0)), 'Respiratory Rate')
        validate_positive_number(int(data.get('vital_hr', 0)), 'Heart Rate')
        validate_positive_number(int(data.get('bp_systolic', 0)), 'BP Systolic')
        validate_positive_number(int(data.get('bp_diastolic', 0)), 'BP Diastolic')
        validate_positive_number(int(data.get('oxygen_sat', 0)), 'O2 Saturation')
        validate_positive_number(float(data.get('bmi_calc', 0)), 'BMI')
        validate_positive_number(float(data.get('birth_weight_g', 0)), 'Birth Weight')
    except ValueError as ve:
        return jsonify({'success': False, 'message': str(ve)}), 400

    if action == 'UPDATE' and not data.get('change_reason'):
        return jsonify({'success': False, 'message': 'Change reason is required when editing'}), 400

    try:
        if action == 'CREATE':
            cursor.execute(
                f"""INSERT INTO delivery
                   (screening_id, facility, dob, age_years, age_months,
                    date_interview, mother_weight, vital_temp, vital_temp_method,
                    vital_rr, vital_hr, bp_systolic, bp_diastolic, oxygen_sat, oxygen_supp,
                    bmi_calc, abnormal_exam, abnormal_specify,
                    delivery_date, delivery_time, delivery_location, delivery_location_other,
                    delivery_provider, delivery_provider_other, mode_delivery,
                    csection_indication, csection_indication_other,
                    birth_weight_g, infant_sex, infant_status, birth_asphyxia,
                    user_initials, timestamp)
                   VALUES ({ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()})""",
                (
                    sid,
                    data.get('facility'),
                    data.get('dob'),
                    int(data.get('age_years', 0)),
                    int(data.get('age_months', 0)),
                    data.get('date_interview'),
                    float(data.get('mother_weight', 0)),
                    float(data.get('vital_temp', 0)),
                    data.get('vital_temp_method'),
                    int(data.get('vital_rr', 0)),
                    int(data.get('vital_hr', 0)),
                    int(data.get('bp_systolic', 0)),
                    int(data.get('bp_diastolic', 0)),
                    int(data.get('oxygen_sat', 0)),
                    data.get('oxygen_supp'),
                    float(data.get('bmi_calc', 0)),
                    data.get('abnormal_exam'),
                    data.get('abnormal_specify'),
                    data.get('delivery_date'),
                    data.get('delivery_time'),
                    data.get('delivery_location'),
                    data.get('delivery_location_other'),
                    data.get('delivery_provider'),
                    data.get('delivery_provider_other'),
                    data.get('mode_delivery'),
                    data.get('csection_indication'),
                    data.get('csection_indication_other'),
                    float(data.get('birth_weight_g', 0)),
                    data.get('infant_sex'),
                    data.get('infant_status'),
                    data.get('birth_asphyxia'),
                    session['user']['initials'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
        else:
            cursor.execute(
                f"""UPDATE delivery SET
                    facility={ph()}, dob={ph()}, age_years={ph()}, age_months={ph()},
                    date_interview={ph()}, mother_weight={ph()}, vital_temp={ph()}, vital_temp_method={ph()},
                    vital_rr={ph()}, vital_hr={ph()}, bp_systolic={ph()}, bp_diastolic={ph()},
                    oxygen_sat={ph()}, oxygen_supp={ph()}, bmi_calc={ph()},
                    abnormal_exam={ph()}, abnormal_specify={ph()},
                    delivery_date={ph()}, delivery_time={ph()}, delivery_location={ph()}, delivery_location_other={ph()},
                    delivery_provider={ph()}, delivery_provider_other={ph()}, mode_delivery={ph()},
                    csection_indication={ph()}, csection_indication_other={ph()},
                    birth_weight_g={ph()}, infant_sex={ph()}, infant_status={ph()}, birth_asphyxia={ph()},
                    user_initials={ph()}, timestamp={ph()}
                    WHERE screening_id={ph()}""",
                (
                    data.get('facility'),
                    data.get('dob'),
                    int(data.get('age_years', 0)),
                    int(data.get('age_months', 0)),
                    data.get('date_interview'),
                    float(data.get('mother_weight', 0)),
                    float(data.get('vital_temp', 0)),
                    data.get('vital_temp_method'),
                    int(data.get('vital_rr', 0)),
                    int(data.get('vital_hr', 0)),
                    int(data.get('bp_systolic', 0)),
                    int(data.get('bp_diastolic', 0)),
                    int(data.get('oxygen_sat', 0)),
                    data.get('oxygen_supp'),
                    float(data.get('bmi_calc', 0)),
                    data.get('abnormal_exam'),
                    data.get('abnormal_specify'),
                    data.get('delivery_date'),
                    data.get('delivery_time'),
                    data.get('delivery_location'),
                    data.get('delivery_location_other'),
                    data.get('delivery_provider'),
                    data.get('delivery_provider_other'),
                    data.get('mode_delivery'),
                    data.get('csection_indication'),
                    data.get('csection_indication_other'),
                    float(data.get('birth_weight_g', 0)),
                    data.get('infant_sex'),
                    data.get('infant_status'),
                    data.get('birth_asphyxia'),
                    session['user']['initials'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    sid
                )
            )
        audit_log('delivery', sid, action, old, data, data.get('change_reason'), session['user']['initials'])
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        logger.error(f"Delivery error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)}), 500

@forms_bp.route('/submit/closeout', methods=['POST'])
def submit_closeout():
    if session['user']['role'] == 'Field Technician':
        return jsonify({'success': False, 'message': 'Write access restricted'}), 403

    data = request.get_json() or {}
    sid = data.get('screening_id')
    if not sid:
        return jsonify({'success': False, 'message': 'Missing screening_id'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM closeout WHERE screening_id = {ph()}", (sid,))
    old = cursor.fetchone()
    action = 'UPDATE' if old else 'CREATE'

    if action == 'UPDATE' and not data.get('change_reason'):
        return jsonify({'success': False, 'message': 'Change reason is required when editing'}), 400

    try:
        if action == 'CREATE':
            cursor.execute(
                f"""INSERT INTO closeout
                   (screening_id, facility, dob, age_years, age_months,
                    date_interview, termination_date, participant_status,
                    discontinuation_reason, discontinuation_specify,
                    user_initials, timestamp)
                   VALUES ({ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()},{ph()})""",
                (
                    sid,
                    data.get('facility'),
                    data.get('dob'),
                    int(data.get('age_years', 0)),
                    int(data.get('age_months', 0)),
                    data.get('date_interview'),
                    data.get('termination_date'),
                    data.get('participant_status'),
                    data.get('discontinuation_reason'),
                    data.get('discontinuation_specify'),
                    session['user']['initials'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
        else:
            cursor.execute(
                f"""UPDATE closeout SET
                    facility={ph()}, dob={ph()}, age_years={ph()}, age_months={ph()},
                    date_interview={ph()}, termination_date={ph()}, participant_status={ph()},
                    discontinuation_reason={ph()}, discontinuation_specify={ph()},
                    user_initials={ph()}, timestamp={ph()}
                    WHERE screening_id={ph()}""",
                (
                    data.get('facility'),
                    data.get('dob'),
                    int(data.get('age_years', 0)),
                    int(data.get('age_months', 0)),
                    data.get('date_interview'),
                    data.get('termination_date'),
                    data.get('participant_status'),
                    data.get('discontinuation_reason'),
                    data.get('discontinuation_specify'),
                    session['user']['initials'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    sid
                )
            )
        audit_log('closeout', sid, action, old, data, data.get('change_reason'), session['user']['initials'])
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        logger.error(f"Closeout error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)}), 500