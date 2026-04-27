# Nexus HR — database setup & seed
# Run once: python database.py
# Re-run to wipe and recreate everything.

import os
import sqlite3

from werkzeug.security import generate_password_hash

DB = os.path.join(os.path.dirname(__file__), 'nexus.db')

SCHEMA = '''
DROP TABLE IF EXISTS announcements;
DROP TABLE IF EXISTS leaves;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS payslips;
DROP TABLE IF EXISTS employees;

CREATE TABLE employees (
    emp_id             TEXT PRIMARY KEY,
    username           TEXT UNIQUE NOT NULL,
    password           TEXT NOT NULL,
    name               TEXT NOT NULL,
    email              TEXT NOT NULL,
    personal_email     TEXT,
    phone              TEXT,
    phone_ext          TEXT,
    dept               TEXT,
    role               TEXT NOT NULL DEFAULT "employee"
                           CHECK (role IN ("employee", "manager", "admin")),
    designation        TEXT,
    manager_id         TEXT REFERENCES employees(emp_id),
    joining_date       TEXT,
    dob                TEXT,
    address            TEXT,
    city               TEXT,
    state              TEXT,
    emergency_contact  TEXT,
    emergency_phone    TEXT,
    blood_group        TEXT,
    avatar_initials    TEXT
);

CREATE TABLE payslips (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id           TEXT    NOT NULL REFERENCES employees(emp_id),
    month            TEXT    NOT NULL,
    month_num        INTEGER NOT NULL,
    year             INTEGER NOT NULL,
    basic            INTEGER NOT NULL,
    hra              INTEGER NOT NULL,
    conveyance       INTEGER NOT NULL,
    medical          INTEGER NOT NULL,
    special          INTEGER NOT NULL,
    gross            INTEGER NOT NULL,
    pf_emp           INTEGER NOT NULL,
    pf_employer      INTEGER NOT NULL,
    income_tax       INTEGER NOT NULL,
    professional_tax INTEGER NOT NULL,
    total_deductions INTEGER NOT NULL,
    net_pay          INTEGER NOT NULL,
    working_days     INTEGER NOT NULL,
    lop_days         INTEGER NOT NULL DEFAULT 0,
    bank_account     TEXT    NOT NULL,
    bank_name        TEXT    NOT NULL
);

CREATE TABLE documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id      TEXT NOT NULL REFERENCES employees(emp_id),
    title       TEXT NOT NULL,
    category    TEXT NOT NULL,
    file_name   TEXT NOT NULL,
    file_size   TEXT NOT NULL,
    uploaded_on TEXT NOT NULL,
    uploaded_by TEXT NOT NULL
);

CREATE TABLE leaves (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id      TEXT NOT NULL REFERENCES employees(emp_id),
    leave_type  TEXT NOT NULL,
    from_date   TEXT NOT NULL,
    to_date     TEXT NOT NULL,
    days        INTEGER NOT NULL,
    reason      TEXT,
    status      TEXT NOT NULL DEFAULT "Pending"
                    CHECK (status IN ("Pending", "Approved", "Rejected")),
    applied_on  TEXT NOT NULL,
    reviewed_by TEXT,
    remarks     TEXT
);

CREATE TABLE announcements (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title     TEXT NOT NULL,
    body      TEXT NOT NULL,
    posted_by TEXT NOT NULL,
    posted_on TEXT NOT NULL,
    category  TEXT NOT NULL DEFAULT "General"
);
'''

# emp_id, username, plain_password,
# name, email, personal_email, phone, phone_ext,
# dept, role, designation, manager_id, joining_date, dob,
# address, city, state, emergency_contact, emergency_phone,
# blood_group, avatar_initials
_EMPLOYEES_RAW = [
    (
        'EMP101', 'arjun.mehta', 'Arjun@2024',
        'Arjun Mehta',
        'arjun.mehta@nexus-corp.in', 'arjun.mehta95@gmail.com',
        '+91 98201 44512', '2201',
        'Information Technology', 'employee', 'Software Engineer',
        'EMP103', '2022-07-11', '1995-04-18',
        'B-12, Sector 62', 'Noida', 'Uttar Pradesh',
        'Kavita Mehta', '+91 98201 44513',
        'B+', 'AM',
    ),
    (
        'EMP102', 'sneha.iyer', 'Sneha@2024',
        'Sneha Iyer',
        'sneha.iyer@nexus-corp.in', 'sneha.iyer1997@yahoo.com',
        '99003-71820', '2202',  # TODO: normalise phone formats across seed data
        'Human Resources', 'employee', 'HR Executive',
        'EMP105', '2021-03-01', '1997-09-23',
        '14, Koramangala 4th Block', 'Bengaluru', 'Karnataka',
        'Ramesh Iyer', '+91 99003 71821',
        'O+', 'SI',
    ),
    (
        'EMP103', 'vikram.nair', 'Vikram@2024',
        'Vikram Nair',
        'vikram.nair@nexus-corp.in', 'vikramnair.personal@gmail.com',
        '+91 97400 88231', '2203',
        'Information Technology', 'manager', 'Engineering Manager',
        'EMP106', '2018-11-19', '1985-12-07',
        'C-407, Hiranandani Gardens', 'Mumbai', 'Maharashtra',
        'Ananya Nair', '+91 97400 88232',
        'A-', 'VN',
    ),
    (
        'EMP104', 'priya.chandran', 'Priya@2024',
        'Priya Chandran',
        'priya.chandran@nexus-corp.in', 'priya.c1998@hotmail.com',
        '+91 91500 23974', '2204',
        'Finance', 'employee', 'Finance Analyst',
        'EMP107', '2023-01-16', '1998-02-14',
        '22, Anna Nagar East', 'Chennai', 'Tamil Nadu',
        'Suresh Chandran', '+91 91500 23975',
        'AB+', 'PC',
    ),
    (
        'EMP105', 'deepa.verma', 'Deepa@2024',
        'Deepa Verma',
        'deepa.verma@nexus-corp.in', 'deepa.verma.hr@gmail.com',
        '+91 88009 54321', '2205',
        'Human Resources', 'manager', 'HR Manager',
        'EMP106', '2017-06-05', '1982-07-30',
        'Flat 3B, Palm Grove Apartments', 'Pune', 'Maharashtra',
        'Rajesh Verma', '+91 88009 54322',
        'B-', 'DV',
    ),
    (
        # director — role normalised to "admin"
        'EMP106', 'rahul.singhania', 'Rahul@2024',
        'Rahul Singhania',
        'rahul.singhania@nexus-corp.in', 'rahulsinghania.dir@gmail.com',
        '+91 98700 12345', '2101',
        'Executive', 'admin', 'Director of Operations',
        None, '2012-04-01', '1978-03-15',
        '5, Golf Links', 'New Delhi', 'Delhi',
        'Meera Singhania', '+91 98700 12346',
        'O-', 'RS',
    ),
    (
        'EMP107', 'anita.kulkarni', 'Anita@2024',
        'Anita Kulkarni',
        'anita.kulkarni@nexus-corp.in', 'anita.kulkarni.fin@gmail.com',
        '+91 93300 67890', '2301',
        'Finance', 'manager', 'Finance Manager',
        'EMP106', '2015-09-14', '1980-11-22',
        'Row House 7, Baner Road', 'Pune', 'Maharashtra',
        'Sunil Kulkarni', '+91 93300 67891',
        'A+', 'AK',
    ),
]


def _hash_employees(raw: list) -> list:
    hashed = []
    for row in raw:
        emp_id, username, plain_pw, *rest = row
        hashed.append((emp_id, username, generate_password_hash(plain_pw), *rest))
    return hashed


PAYSLIPS = [
    # emp_id, month, month_num, year,
    # basic, hra, conveyance, medical, special, gross,
    # pf_emp, pf_employer, income_tax, professional_tax, total_deductions,
    # net_pay, working_days, lop_days, bank_account, bank_name

    # Arjun Mehta — EMP101
    ('EMP101', 'March',    3, 2025, 35000, 14000, 1600, 1250, 6150,  58000, 4200, 4200, 2800, 200, 7200,  50800, 26, 0, 'XXXX XXXX 4821', 'HDFC Bank'),
    ('EMP101', 'February', 2, 2025, 35000, 14000, 1600, 1250, 6150,  58000, 4200, 4200, 2800, 200, 7200,  50800, 24, 0, 'XXXX XXXX 4821', 'HDFC Bank'),
    ('EMP101', 'January',  1, 2025, 35000, 14000, 1600, 1250, 6150,  58000, 4200, 4200, 2800, 200, 7200,  50800, 27, 0, 'XXXX XXXX 4821', 'HDFC Bank'),
    ('EMP101', 'December', 12, 2024, 35000, 14000, 1600, 1250, 6150, 58000, 4200, 4200, 2800, 200, 7200,  50800, 26, 0, 'XXXX XXXX 4821', 'HDFC Bank'),
    ('EMP101', 'November', 11, 2024, 35000, 14000, 1600, 1250, 6150, 58000, 4200, 4200, 2800, 200, 7200,  50800, 25, 0, 'XXXX XXXX 4821', 'HDFC Bank'),

    # Sneha Iyer — EMP102
    ('EMP102', 'March',    3, 2025, 32000, 12800, 1600, 1250, 4350,  52000, 3840, 3840, 1800, 200, 5840,  46160, 26, 0, 'XXXX XXXX 7734', 'ICICI Bank'),
    ('EMP102', 'February', 2, 2025, 32000, 12800, 1600, 1250, 4350,  52000, 3840, 3840, 1800, 200, 5840,  46160, 24, 0, 'XXXX XXXX 7734', 'ICICI Bank'),
    ('EMP102', 'January',  1, 2025, 32000, 12800, 1600, 1250, 4350,  52000, 3840, 3840, 1800, 200, 5840,  46160, 27, 0, 'XXXX XXXX 7734', 'ICICI Bank'),
    ('EMP102', 'December', 12, 2024, 32000, 12800, 1600, 1250, 4350, 52000, 3840, 3840, 1800, 200, 5840,  46160, 26, 0, 'XXXX XXXX 7734', 'ICICI Bank'),

    # Vikram Nair — EMP103
    ('EMP103', 'March',    3, 2025, 70000, 28000, 1600, 1250, 19150, 120000, 8400, 8400, 9500, 200, 18100, 101900, 26, 0, 'XXXX XXXX 3391', 'Axis Bank'),
    ('EMP103', 'February', 2, 2025, 70000, 28000, 1600, 1250, 19150, 120000, 8400, 8400, 9500, 200, 18100, 101900, 24, 0, 'XXXX XXXX 3391', 'Axis Bank'),
    ('EMP103', 'January',  1, 2025, 70000, 28000, 1600, 1250, 19150, 120000, 8400, 8400, 9500, 200, 18100, 101900, 27, 0, 'XXXX XXXX 3391', 'Axis Bank'),
    ('EMP103', 'December', 12, 2024, 70000, 28000, 1600, 1250, 19150, 120000, 8400, 8400, 9500, 200, 18100, 101900, 26, 0, 'XXXX XXXX 3391', 'Axis Bank'),

    # Priya Chandran — EMP104
    ('EMP104', 'March',    3, 2025, 30000, 12000, 1600, 1250, 5150,  50000, 3600, 3600, 1500, 200, 5300,  44700, 26, 0, 'XXXX XXXX 8812', 'SBI'),
    ('EMP104', 'February', 2, 2025, 30000, 12000, 1600, 1250, 5150,  50000, 3600, 3600, 1500, 200, 5300,  44700, 24, 0, 'XXXX XXXX 8812', 'SBI'),
    ('EMP104', 'January',  1, 2025, 30000, 12000, 1600, 1250, 5150,  50000, 3600, 3600, 1500, 200, 5300,  44700, 27, 0, 'XXXX XXXX 8812', 'SBI'),

    # Deepa Verma — EMP105
    ('EMP105', 'March',    3, 2025, 60000, 24000, 1600, 1250, 13150, 100000, 7200, 7200, 7200, 200, 14600, 85400, 26, 0, 'XXXX XXXX 5567', 'Kotak Bank'),
    ('EMP105', 'February', 2, 2025, 60000, 24000, 1600, 1250, 13150, 100000, 7200, 7200, 7200, 200, 14600, 85400, 24, 0, 'XXXX XXXX 5567', 'Kotak Bank'),
    ('EMP105', 'January',  1, 2025, 60000, 24000, 1600, 1250, 13150, 100000, 7200, 7200, 7200, 200, 14600, 85400, 27, 0, 'XXXX XXXX 5567', 'Kotak Bank'),

    # Rahul Singhania — EMP106
    ('EMP106', 'March',    3, 2025, 175000, 70000, 1600, 1250, 52150, 300000, 21000, 21000, 52000, 200, 73200, 226800, 26, 0, 'XXXX XXXX 1001', 'HDFC Bank'),
    ('EMP106', 'February', 2, 2025, 175000, 70000, 1600, 1250, 52150, 300000, 21000, 21000, 52000, 200, 73200, 226800, 24, 0, 'XXXX XXXX 1001', 'HDFC Bank'),
    ('EMP106', 'January',  1, 2025, 175000, 70000, 1600, 1250, 52150, 300000, 21000, 21000, 52000, 200, 73200, 226800, 27, 0, 'XXXX XXXX 1001', 'HDFC Bank'),

    # Anita Kulkarni — EMP107
    ('EMP107', 'March',    3, 2025, 80000, 32000, 1600, 1250, 25150, 140000, 9600, 9600, 12000, 200, 21800, 118200, 26, 0, 'XXXX XXXX 6643', 'ICICI Bank'),
    ('EMP107', 'February', 2, 2025, 80000, 32000, 1600, 1250, 25150, 140000, 9600, 9600, 12000, 200, 21800, 118200, 24, 0, 'XXXX XXXX 6643', 'ICICI Bank'),
    ('EMP107', 'January',  1, 2025, 80000, 32000, 1600, 1250, 25150, 140000, 9600, 9600, 12000, 200, 21800, 118200, 27, 0, 'XXXX XXXX 6643', 'ICICI Bank'),
]

DOCUMENTS = [
    # emp_id, title, category, file_name, file_size, uploaded_on, uploaded_by

    # EMP101 — Arjun
    ('EMP101', 'Offer Letter — Software Engineer',  'Offer Letter',   'offer_letter_EMP101.pdf',        '189 KB', '2022-07-01', 'sneha.iyer'),
    ('EMP101', 'Appointment Letter',                'Appointment',    'appointment_EMP101.pdf',          '204 KB', '2022-07-11', 'sneha.iyer'),
    ('EMP101', 'PAN Card Copy',                     'ID Proof',       'pan_EMP101.pdf',                  '512 KB', '2022-07-11', 'arjun.mehta'),
    ('EMP101', 'Aadhaar Card Copy',                 'ID Proof',       'aadhaar_EMP101.pdf',              '480 KB', '2022-07-11', 'arjun.mehta'),
    ('EMP101', 'Appraisal Letter FY 2023-24',       'Appraisal',      'appraisal_EMP101_FY2324.pdf',     '167 KB', '2024-04-01', 'deepa.verma'),
    ('EMP101', 'Increment Letter — 14% Hike',       'Salary Revision','increment_EMP101_2024.pdf',       '143 KB', '2024-04-01', 'deepa.verma'),
    ('EMP101', 'Relieving Letter — Previous Employer','Background',   'relieving_prev_EMP101.pdf',       '230 KB', '2022-07-08', 'sneha.iyer'),

    # EMP102 — Sneha
    ('EMP102', 'Offer Letter — HR Executive',       'Offer Letter',   'offer_letter_EMP102.pdf',         '176 KB', '2021-02-20', 'deepa.verma'),
    ('EMP102', 'Appointment Letter',                'Appointment',    'appointment_EMP102.pdf',          '198 KB', '2021-03-01', 'deepa.verma'),
    ('EMP102', 'PAN Card Copy',                     'ID Proof',       'pan_EMP102.pdf',                  '498 KB', '2021-03-01', 'sneha.iyer'),
    ('EMP102', 'Medical Certificate — Feb 2025',    'Medical',        'medical_EMP102_feb2025.pdf',      '310 KB', '2025-02-06', 'sneha.iyer'),
    ('EMP102', 'Appraisal Letter FY 2023-24',       'Appraisal',      'appraisal_EMP102_FY2324.pdf',     '161 KB', '2024-04-01', 'deepa.verma'),

    # EMP103 — Vikram
    ('EMP103', 'Appointment Letter — Manager',      'Appointment',    'appointment_EMP103.pdf',          '215 KB', '2018-11-19', 'deepa.verma'),
    ('EMP103', 'Promotion Letter — Engineering Manager','Promotion',  'promotion_EMP103_2021.pdf',       '188 KB', '2021-06-01', 'deepa.verma'),
    ('EMP103', 'Appraisal Letter FY 2023-24',       'Appraisal',      'appraisal_EMP103_FY2324.pdf',     '174 KB', '2024-04-01', 'deepa.verma'),
    ('EMP103', 'Annual CTC Breakup 2024-25',        'Salary Structure','ctc_EMP103_FY2425.pdf',          '156 KB', '2024-04-01', 'deepa.verma'),
    ('EMP103', 'ESOP Grant Letter — 500 Units',     'ESOP',           'esop_EMP103_2023.pdf',            '340 KB', '2023-01-15', 'rahul.singhania'),
    ('EMP103', 'Background Verification Report',    'Background',     'bgv_EMP103.pdf',                  '890 KB', '2018-11-15', 'sneha.iyer'),

    # EMP104 — Priya
    ('EMP104', 'Offer Letter — Finance Analyst',    'Offer Letter',   'offer_letter_EMP104.pdf',         '181 KB', '2023-01-05', 'sneha.iyer'),
    ('EMP104', 'Appointment Letter',                'Appointment',    'appointment_EMP104.pdf',          '196 KB', '2023-01-16', 'sneha.iyer'),
    ('EMP104', 'PAN Card Copy',                     'ID Proof',       'pan_EMP104.pdf',                  '503 KB', '2023-01-16', 'priya.chandran'),
    ('EMP104', 'Medical Certificate — Hospitalisation Dec 2024','Medical','medical_EMP104_dec2024.pdf', '290 KB', '2024-12-23', 'sneha.iyer'),
    ('EMP104', 'Appraisal Letter FY 2023-24',       'Appraisal',      'appraisal_EMP104_FY2324.pdf',     '155 KB', '2024-04-01', 'deepa.verma'),

    # EMP105 — Deepa
    ('EMP105', 'Appointment Letter — HR Manager',   'Appointment',    'appointment_EMP105.pdf',          '210 KB', '2017-06-05', 'rahul.singhania'),
    ('EMP105', 'Promotion Letter — HR Manager',     'Promotion',      'promotion_EMP105_2019.pdf',       '192 KB', '2019-08-01', 'rahul.singhania'),
    ('EMP105', 'Annual CTC Breakup 2024-25',        'Salary Structure','ctc_EMP105_FY2425.pdf',          '148 KB', '2024-04-01', 'rahul.singhania'),
    ('EMP105', 'Appraisal Letter FY 2023-24',       'Appraisal',      'appraisal_EMP105_FY2324.pdf',     '170 KB', '2024-04-01', 'rahul.singhania'),

    # EMP106 — Rahul
    ('EMP106', 'Director Appointment Agreement',    'Legal Agreement','dir_agreement_EMP106.pdf',        '1.2 MB', '2012-04-01', 'legal'),
    ('EMP106', 'Employment Contract 2024-25',       'Contract',       'contract_EMP106_FY2425.pdf',      '980 KB', '2024-04-01', 'legal'),
    ('EMP106', 'ESOP Grant Letter — 5000 Units',    'ESOP',           'esop_EMP106_2022.pdf',            '420 KB', '2022-01-01', 'legal'),
    ('EMP106', 'Annual CTC Breakup 2024-25',        'Salary Structure','ctc_EMP106_FY2425.pdf',          '220 KB', '2024-04-01', 'anita.kulkarni'),
    ('EMP106', 'Board Resolution — Director Remuneration','Board Document','board_res_EMP106_2024.pdf', '560 KB', '2024-03-15', 'legal'),

    # EMP107 — Anita
    ('EMP107', 'Appointment Letter — Finance Manager','Appointment',  'appointment_EMP107.pdf',          '208 KB', '2015-09-14', 'deepa.verma'),
    ('EMP107', 'Annual CTC Breakup 2024-25',        'Salary Structure','ctc_EMP107_FY2425.pdf',          '152 KB', '2024-04-01', 'deepa.verma'),
    ('EMP107', 'Appraisal Letter FY 2023-24',       'Appraisal',      'appraisal_EMP107_FY2324.pdf',     '166 KB', '2024-04-01', 'deepa.verma'),
]

LEAVES = [
    # emp_id, leave_type, from_date, to_date, days, reason, status, applied_on, reviewed_by, remarks

    # Arjun — EMP101
    ('EMP101', 'Annual Leave',  '2025-01-13', '2025-01-14', 2, 'Attending cousins wedding in Jaipur',   'Approved', '2025-01-08', 'vikram.nair',     None),
    ('EMP101', 'Sick Leave',    '2025-02-19', '2025-02-19', 1, 'High fever and cold',                   'Approved', '2025-02-19', 'vikram.nair',     None),
    ('EMP101', 'Annual Leave',  '2024-12-23', '2024-12-27', 5, 'Year-end family vacation',              'Approved', '2024-12-15', 'vikram.nair',     None),
    ('EMP101', 'Casual Leave',  '2025-03-28', '2025-03-28', 1, 'Personal errand',                       'Pending',  '2025-03-25', None,              None),

    # Sneha — EMP102
    ('EMP102', 'Sick Leave',    '2025-02-04', '2025-02-06', 3, 'Viral fever — doctor advised rest for 3 days', 'Approved', '2025-02-04', 'deepa.verma', None),
    ('EMP102', 'Annual Leave',  '2024-11-01', '2024-11-03', 3, 'Diwali celebrations at hometown',       'Approved', '2024-10-25', 'deepa.verma',     None),
    ('EMP102', 'Medical Leave', '2024-08-12', '2024-08-15', 4, 'Minor procedure — confidential',        'Approved', '2024-08-10', 'deepa.verma',     'Approved with medical certificate'),
    ('EMP102', 'Annual Leave',  '2025-04-18', '2025-04-19', 2, 'Eid-ul-Fitr holiday',                  'Pending',  '2025-04-10', None,              None),

    # Vikram — EMP103
    ('EMP103', 'Annual Leave',      '2024-09-30', '2024-10-04', 5, 'International conference — Singapore', 'Approved', '2024-09-20', 'rahul.singhania', None),
    ('EMP103', 'Annual Leave',      '2024-12-31', '2025-01-01', 2, 'New Year break',                       'Approved', '2024-12-20', 'rahul.singhania', None),
    ('EMP103', 'Sick Leave',        '2025-02-24', '2025-02-25', 2, 'Back pain — physiotherapy',            'Approved', '2025-02-24', 'rahul.singhania', None),
    ('EMP103', 'Compensatory Leave','2025-03-15', '2025-03-15', 1, 'Comp off — worked on Holi',            'Approved', '2025-03-16', 'rahul.singhania', None),

    # Priya — EMP104
    ('EMP104', 'Sick Leave',    '2024-11-20', '2024-11-22', 3, 'Dengue fever — hospitalised',           'Approved', '2024-11-20', 'anita.kulkarni',  'Get well soon. Medical certificate received.'),
    ('EMP104', 'Medical Leave', '2024-12-18', '2024-12-23', 6, 'Appendicitis — emergency surgery',      'Approved', '2024-12-18', 'anita.kulkarni',  'Approved. Hospital discharge summary submitted.'),
    ('EMP104', 'Annual Leave',  '2025-01-26', '2025-01-26', 1, 'Republic Day — extended weekend',       'Approved', '2025-01-22', 'anita.kulkarni',  None),
    ('EMP104', 'Casual Leave',  '2025-03-05', '2025-03-05', 1, 'Passport renewal appointment',          'Rejected', '2025-03-04', 'anita.kulkarni',  'Not approved — month-end closing period'),

    # Deepa — EMP105
    ('EMP105', 'Annual Leave', '2024-10-14', '2024-10-16', 3, 'Navratri holiday trip',  'Approved', '2024-10-07', 'rahul.singhania', None),
    ('EMP105', 'Annual Leave', '2024-12-24', '2024-12-26', 3, 'Christmas holiday',      'Approved', '2024-12-18', 'rahul.singhania', None),
    ('EMP105', 'Sick Leave',   '2025-01-15', '2025-01-16', 2, 'Migraine attack',        'Approved', '2025-01-15', 'rahul.singhania', None),

    # Rahul — EMP106
    ('EMP106', 'Annual Leave', '2024-08-12', '2024-08-16', 5,  'Family vacation — Europe', 'Approved', '2024-07-25', None, None),
    ('EMP106', 'Annual Leave', '2024-12-22', '2025-01-02', 12, 'Year-end holiday',         'Approved', '2024-12-10', None, None),

    # Anita — EMP107
    ('EMP107', 'Annual Leave', '2024-10-02', '2024-10-04', 3, 'Dussehra holidays',               'Approved', '2024-09-25', 'rahul.singhania', None),
    ('EMP107', 'Annual Leave', '2025-01-14', '2025-01-15', 2, 'Makar Sankranti — family function','Approved', '2025-01-10', 'rahul.singhania', None),
    ('EMP107', 'Sick Leave',   '2025-02-11', '2025-02-11', 1, 'Severe headache',                 'Approved', '2025-02-11', 'rahul.singhania', None),
]

ANNOUNCEMENTS = [
    (
        'Annual Appraisal Cycle FY 2024-25 Now Open',
        'The annual performance appraisal cycle for FY 2024-25 is now open. '
        'All employees must complete their self-assessment by 31st March 2025. '
        'Managers are requested to schedule review meetings by 10th April 2025. '
        'Login to the HR portal and navigate to Performance → Self Appraisal to get started.',
        'deepa.verma', '2025-03-01', 'HR',
    ),
    (
        'Office Closure — Holi (14th March 2025)',
        'The Nexus Corp offices will remain closed on Friday, 14th March 2025 on account of Holi. '
        'All employees are advised to plan project deliverables accordingly. '
        'Emergency escalations may be directed to your respective on-call lead.',
        'rahul.singhania', '2025-03-10', 'General',
    ),
    (
        'Updated Leave Policy — Effective 1st April 2025',
        'Following the HR policy review, the Casual Leave entitlement has been revised from '
        '7 days to 9 days per calendar year effective 1st April 2025. '
        'The Earned Leave accumulation cap has been increased to 45 days. '
        'Detailed policy document will be circulated by the HR team shortly.',
        'deepa.verma', '2025-02-20', 'HR',
    ),
    (
        'Town Hall — Q4 Business Review (21st March)',
        'The All-Hands Town Hall for Q4 FY2024-25 Business Review will be held on '
        'Friday, 21st March 2025 at 3:00 PM in the Main Conference Hall (3rd Floor). '
        'Remote employees can join via the meeting link shared separately. '
        'Attendance is mandatory for all employees.',
        'rahul.singhania', '2025-03-14', 'General',
    ),
    (
        'New IT Asset Request Process',
        'Effective immediately, all IT asset requests (laptops, monitors, peripherals) '
        'must be raised through the IT Service Desk portal at it-helpdesk.nexus-corp.in. '
        'Direct requests to the IT team will not be entertained. '
        'Standard turnaround time is 5 working days.',
        'vikram.nair', '2025-02-28', 'IT',
    ),
]


def main() -> None:
    if os.path.exists(DB):
        os.remove(DB)
        print(f'Removed existing database: {DB}')

    conn = sqlite3.connect(DB)
    conn.execute('PRAGMA foreign_keys = ON')
    conn.executescript(SCHEMA)

    print('Hashing passwords...')
    employees = _hash_employees(_EMPLOYEES_RAW)

    # disable FK enforcement temporarily so manager_id forward refs don't break insertion order
    conn.execute('PRAGMA foreign_keys = OFF')
    conn.executemany(
        'INSERT INTO employees VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        employees,
    )
    conn.execute('PRAGMA foreign_keys = ON')

    conn.executemany(
        '''INSERT INTO payslips
           (emp_id, month, month_num, year,
            basic, hra, conveyance, medical, special, gross,
            pf_emp, pf_employer, income_tax, professional_tax, total_deductions,
            net_pay, working_days, lop_days, bank_account, bank_name)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        PAYSLIPS,
    )

    conn.executemany(
        'INSERT INTO documents (emp_id, title, category, file_name, file_size, uploaded_on, uploaded_by) '
        'VALUES (?,?,?,?,?,?,?)',
        DOCUMENTS,
    )

    conn.executemany(
        'INSERT INTO leaves (emp_id, leave_type, from_date, to_date, days, reason, status, applied_on, reviewed_by, remarks) '
        'VALUES (?,?,?,?,?,?,?,?,?,?)',
        LEAVES,
    )

    conn.executemany(
        'INSERT INTO announcements (title, body, posted_by, posted_on, category) VALUES (?,?,?,?,?)',
        ANNOUNCEMENTS,
    )

    conn.commit()
    conn.close()

    print(f'\nDatabase ready: {DB}')
    print('\nTest accounts:')
    print(f'  {"Username":<22}  {"Password":<15}  {"Emp ID":<8}  Role')
    print(f'  {"-"*22}  {"-"*15}  {"-"*8}  ----')
    for row in _EMPLOYEES_RAW:
        emp_id, username, plain_pw = row[0], row[1], row[2]
        role = row[9]
        print(f'  {username:<22}  {plain_pw:<15}  {emp_id:<8}  {role}')


if __name__ == '__main__':
    main()
