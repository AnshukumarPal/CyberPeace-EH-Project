# Nexus HR — Internal Employee Portal
# Flask backend
#
# Setup:
#   1. pip install -r requirements.txt
#   2. cp .env.example .env  &&  edit .env
#   3. python database.py
#   4. python app.py
#   5. Open http://localhost:5000

import os
import sqlite3
import logging
from functools import wraps
from datetime import date

from flask import Flask, request, jsonify, session, render_template
from werkzeug.security import check_password_hash

from config import get_config

app = Flask(__name__)
app.config.from_object(get_config())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
)
log = logging.getLogger(__name__)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(app.config['DB_PATH'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


# auth helpers

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'emp_id' not in session:
            return jsonify({'error': 'Authentication required.'}), 401
        return f(*args, **kwargs)
    return decorated


def _session_role() -> str:
    return session.get('role', 'employee')


def _is_direct_report(manager_id: str, target_emp_id: str, conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        'SELECT 1 FROM employees WHERE emp_id = ? AND manager_id = ?',
        (target_emp_id, manager_id)
    ).fetchone()
    return row is not None


def can_read_employee_data(target_emp_id: str, conn: sqlite3.Connection) -> bool:
    # self, admin, or manager of the target
    requester_id = session['emp_id']
    role = _session_role()

    if requester_id == target_emp_id:
        return True
    if role == 'admin':
        return True
    if role == 'manager' and _is_direct_report(requester_id, target_emp_id, conn):
        return True
    return False


def can_write_employee_data(target_emp_id: str) -> bool:
    # managers can't edit subordinate records here, only self or admin
    requester_id = session['emp_id']
    role = _session_role()
    return requester_id == target_emp_id or role == 'admin'


# input helpers

def _str(value, max_len: int = 255) -> str:
    return str(value or '').strip()[:max_len]


ALLOWED_LEAVE_TYPES = {
    'Annual Leave', 'Sick Leave', 'Casual Leave',
    'Medical Leave', 'Compensatory Leave', 'Maternity Leave',
    'Paternity Leave', 'Unpaid Leave',
}


def _validate_date(value: str, field: str) -> tuple:
    try:
        parsed = date.fromisoformat(value)
        return str(parsed), None
    except (TypeError, ValueError):
        return None, (jsonify({'error': f"'{field}' must be a valid ISO date (YYYY-MM-DD)."}), 422)


# routes

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/auth/login', methods=['POST'])
def login():
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({'error': 'Request body must be valid JSON.'}), 400

    username = _str(body.get('username'), 80)
    password = _str(body.get('password'), 128)

    if not username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400

    conn = get_db()
    try:
        row = conn.execute(
            'SELECT * FROM employees WHERE username = ?',
            (username,)
        ).fetchone()
    finally:
        conn.close()

    # timing-safe; don't split the error by field
    if row is None or not check_password_hash(row['password'], password):
        log.warning('failed login for username=%r', username)
        return jsonify({'error': 'Invalid username or password.'}), 401

    session.clear()
    session['emp_id']   = row['emp_id']
    session['username'] = row['username']
    session['name']     = row['name']
    session['role']     = row['role']

    log.info('login: emp_id=%s username=%s', row['emp_id'], row['username'])

    return jsonify({
        'emp_id': row['emp_id'],
        'name':   row['name'],
        'role':   row['role'],
        'dept':   row['dept'],
        'avatar': row['avatar_initials'],
    }), 200


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    emp_id = session.get('emp_id', '<anonymous>')
    session.clear()
    log.info('logout: emp_id=%s', emp_id)
    return jsonify({'ok': True}), 200


@app.route('/api/auth/me')
@login_required
def me():
    conn = get_db()
    try:
        row = conn.execute(
            'SELECT emp_id, name, role, dept, avatar_initials FROM employees WHERE emp_id = ?',
            (session['emp_id'],)
        ).fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({'error': 'Employee record not found.'}), 404
    return jsonify(dict(row)), 200


@app.route('/api/dashboard')
@login_required
def dashboard():
    emp_id = session['emp_id']
    conn   = get_db()
    try:
        pending_leaves = conn.execute(
            'SELECT COUNT(*) AS c FROM leaves WHERE emp_id = ? AND status = "Pending"',
            (emp_id,)
        ).fetchone()['c']

        latest_pay = conn.execute(
            'SELECT net_pay, month, year FROM payslips '
            'WHERE emp_id = ? ORDER BY year DESC, month_num DESC LIMIT 1',
            (emp_id,)
        ).fetchone()

        doc_count = conn.execute(
            'SELECT COUNT(*) AS c FROM documents WHERE emp_id = ?',
            (emp_id,)
        ).fetchone()['c']

        announcements = conn.execute(
            'SELECT * FROM announcements ORDER BY posted_on DESC LIMIT 5'
        ).fetchall()
    finally:
        conn.close()

    return jsonify({
        'pending_leaves': pending_leaves,
        'latest_pay':     dict(latest_pay) if latest_pay else None,
        'doc_count':      doc_count,
        'announcements':  [dict(a) for a in announcements],
    }), 200


@app.route('/api/directory')
@login_required
def directory():
    # only non-sensitive columns -- no salary, dob, address etc.
    conn = get_db()
    try:
        rows = conn.execute(
            'SELECT emp_id, name, dept, role, designation, email, phone_ext '
            'FROM employees ORDER BY name'
        ).fetchall()
    finally:
        conn.close()
    return jsonify([dict(r) for r in rows]), 200


@app.route('/api/employees/<emp_id>/profile')
@login_required
def get_profile(emp_id: str):
    conn = get_db()
    try:
        if not can_read_employee_data(emp_id, conn):
            log.warning('unauthorized profile read: user=%s target=%s', session['emp_id'], emp_id)
            return jsonify({'error': 'Access denied.'}), 403

        row = conn.execute(
            '''SELECT emp_id, name, email, personal_email, phone, phone_ext,
                      dept, role, designation, manager_id, joining_date, dob,
                      address, city, state, emergency_contact, emergency_phone,
                      blood_group, avatar_initials
               FROM employees WHERE emp_id = ?''',
            (emp_id,)
        ).fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({'error': 'Employee not found.'}), 404
    return jsonify(dict(row)), 200


@app.route('/api/employees/<emp_id>/profile', methods=['PUT'])
@login_required
def update_profile(emp_id: str):
    if not can_write_employee_data(emp_id):
        log.warning('unauthorized profile update: user=%s target=%s', session['emp_id'], emp_id)
        return jsonify({'error': 'Access denied.'}), 403

    body = request.get_json(silent=True)
    if body is None:
        return jsonify({'error': 'Request body must be valid JSON.'}), 400

    # only fields the employee can self-update; role/dept/salary etc. not accepted here
    phone   = _str(body.get('phone'), 20)
    addr    = _str(body.get('address'), 255)
    city    = _str(body.get('city'), 100)
    emrg    = _str(body.get('emergency_contact'), 100)
    emrg_ph = _str(body.get('emergency_phone'), 20)

    conn = get_db()
    try:
        affected = conn.execute(
            'UPDATE employees '
            'SET phone=?, address=?, city=?, emergency_contact=?, emergency_phone=? '
            'WHERE emp_id=?',
            (phone, addr, city, emrg, emrg_ph, emp_id)
        ).rowcount
        conn.commit()
    finally:
        conn.close()

    if affected == 0:
        return jsonify({'error': 'Employee not found.'}), 404

    log.info('profile updated: emp_id=%s by=%s', emp_id, session['emp_id'])
    return jsonify({'ok': True}), 200


@app.route('/api/employees/<emp_id>/payslips')
@login_required
def get_payslips(emp_id: str):
    conn = get_db()
    try:
        if not can_read_employee_data(emp_id, conn):
            log.warning('unauthorized payslip access: user=%s target=%s', session['emp_id'], emp_id)
            return jsonify({'error': 'Access denied.'}), 403

        rows = conn.execute(
            'SELECT * FROM payslips WHERE emp_id = ? ORDER BY year DESC, month_num DESC',
            (emp_id,)
        ).fetchall()
    finally:
        conn.close()

    # TODO: maybe paginate this at some point
    if not rows:
        return jsonify({'error': 'No payslip records found.'}), 404
    return jsonify([dict(r) for r in rows]), 200


@app.route('/api/employees/<emp_id>/documents')
@login_required
def get_documents(emp_id: str):
    conn = get_db()
    try:
        if not can_read_employee_data(emp_id, conn):
            log.warning('unauthorized document access: user=%s target=%s', session['emp_id'], emp_id)
            return jsonify({'error': 'Access denied.'}), 403

        rows = conn.execute(
            'SELECT * FROM documents WHERE emp_id = ? ORDER BY uploaded_on DESC',
            (emp_id,)
        ).fetchall()
    finally:
        conn.close()

    return jsonify([dict(r) for r in rows]), 200


@app.route('/api/employees/<emp_id>/leaves')
@login_required
def get_leaves(emp_id: str):
    conn = get_db()
    try:
        if not can_read_employee_data(emp_id, conn):
            log.warning('unauthorized leave access: user=%s target=%s', session['emp_id'], emp_id)
            return jsonify({'error': 'Access denied.'}), 403

        rows = conn.execute(
            'SELECT * FROM leaves WHERE emp_id = ? ORDER BY applied_on DESC',
            (emp_id,)
        ).fetchall()
    finally:
        conn.close()

    return jsonify([dict(r) for r in rows]), 200


@app.route('/api/employees/<emp_id>/leaves', methods=['POST'])
@login_required
def apply_leave(emp_id: str):
    if not can_write_employee_data(emp_id):
        log.warning('unauthorized leave application: user=%s target=%s', session['emp_id'], emp_id)
        return jsonify({'error': 'Access denied.'}), 403

    body = request.get_json(silent=True)
    if not body:
        return jsonify({'error': 'Request body must be valid JSON.'}), 400

    leave_type = _str(body.get('leave_type'), 50)
    if leave_type not in ALLOWED_LEAVE_TYPES:
        return jsonify({
            'error': 'Invalid leave_type.',
            'allowed': sorted(ALLOWED_LEAVE_TYPES),
        }), 422

    from_date, err = _validate_date(body.get('from_date'), 'from_date')
    if err:
        return err
    to_date, err = _validate_date(body.get('to_date'), 'to_date')
    if err:
        return err

    if from_date > to_date:
        return jsonify({'error': "'from_date' must not be after 'to_date'."}), 422

    try:
        days = int(body.get('days', 1))
        if days < 1 or days > 365:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'error': "'days' must be a positive integer (1–365)."}), 422

    reason = _str(body.get('reason', ''), 500)

    conn = get_db()
    try:
        conn.execute(
            '''INSERT INTO leaves
               (emp_id, leave_type, from_date, to_date, days, reason, status, applied_on)
               VALUES (?, ?, ?, ?, ?, ?, "Pending", date("now"))''',
            (emp_id, leave_type, from_date, to_date, days, reason)
        )
        conn.commit()
    finally:
        conn.close()

    log.info('leave applied: emp_id=%s type=%s %s->%s days=%d by=%s',
             emp_id, leave_type, from_date, to_date, days, session['emp_id'])
    return jsonify({'ok': True, 'message': 'Leave application submitted successfully.'}), 201


# error handlers

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found.'}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'error': 'Method not allowed.'}), 405


@app.errorhandler(500)
def internal_error(e):
    log.exception('unhandled server error')
    return jsonify({'error': 'An internal server error occurred.'}), 500


if __name__ == '__main__':
    db_path = app.config['DB_PATH']
    if not os.path.exists(db_path):
        print('\n[!] Database not found. Run:  python database.py\n')
    else:
        print('\n  Nexus HR — Internal Portal')
        print('  http://localhost:5000\n')
    app.run(host='127.0.0.1', port=5000)
