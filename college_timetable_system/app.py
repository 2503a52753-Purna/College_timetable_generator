from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import sqlite3
import random
import os
from functools import wraps
from pathlib import Path
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(32)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', '0') == '1'
DB_NAME = Path(__file__).resolve().parent / 'database.db'
REQUIRED_DEPARTMENTS = [
    'Civil Engineering',
    'Computer Science and Engineering',
    'Electronics and Electronics Engineering',
    'Mechanical Engineering',
    'Pharmacy',
]
SECTION_CODES = {
    'Computer Science and Engineering': 'CSE',
    'Electronics and Electronics Engineering': 'EEE',
    'Civil Engineering': 'CIV',
    'Mechanical Engineering': 'MEC',
    'Pharmacy': 'PHA',
}
SUBJECT_TEMPLATES = {
    'Computer Science and Engineering': ('Programming', 'Data Structures', 'Computer Networks'),
    'Electronics and Electronics Engineering': ('Digital Systems', 'Signals and Systems', 'Microprocessors'),
    'Civil Engineering': ('Structural Analysis', 'Surveying', 'Concrete Technology'),
    'Mechanical Engineering': ('Thermodynamics', 'Machine Design', 'Manufacturing Processes'),
    'Pharmacy': ('Pharmacology', 'Medicinal Chemistry', 'Pharmaceutics'),
}
DEPARTMENT_ALIASES = {
    'Computer Science': 'Computer Science and Engineering',
    'Electrical and Electronic': 'Electrical and Electronics Engineering',
    'Electronics and Communication Engineering': 'Electronics and Electronics Engineering',
}

def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get('is_admin'):
            if request.path.startswith('/api/'):
                return jsonify({'status': 'error', 'message': 'Admin authentication required.'}), 401
            return redirect(url_for('admin_login', next=request.path))
        return view(*args, **kwargs)
    return wrapped_view

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def is_super_admin():
    return session.get('admin_role') == 'super'


def get_accessible_college_ids():
    if not session.get('is_admin'):
        return []
    if is_super_admin():
        with get_db() as conn:
            return [row['id'] for row in conn.execute('SELECT id FROM colleges ORDER BY id')]

    admin_user_id = session.get('admin_user_id')
    if admin_user_id is not None:
        with get_db() as conn:
            rows = conn.execute(
                'SELECT college_id FROM admin_college_access WHERE admin_user_id = ?',
                (admin_user_id,),
            ).fetchall()
            ids = [row['college_id'] for row in rows]
            if ids:
                return ids

    selected = session.get('admin_college_id')
    return [selected] if selected is not None else []


def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS colleges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                short_name TEXT,
                location TEXT,
                logo_url TEXT,
                website TEXT,
                is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                college_id INTEGER,
                FOREIGN KEY(college_id) REFERENCES colleges(id)
            );
            CREATE TABLE IF NOT EXISTS sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department_id INTEGER,
                college_id INTEGER,
                FOREIGN KEY(department_id) REFERENCES departments(id),
                FOREIGN KEY(college_id) REFERENCES colleges(id)
            );
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department_id INTEGER,
                hours_per_week INTEGER NOT NULL,
                is_lab INTEGER DEFAULT 0,
                FOREIGN KEY(department_id) REFERENCES departments(id)
            );
            CREATE TABLE IF NOT EXISTS faculty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department_id INTEGER,
                subject_id INTEGER,
                availability TEXT,
                FOREIGN KEY(department_id) REFERENCES departments(id),
                FOREIGN KEY(subject_id) REFERENCES subjects(id)
            );
            CREATE TABLE IF NOT EXISTS classrooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                college_id INTEGER,
                is_lab INTEGER DEFAULT 0,
                capacity INTEGER NOT NULL,
                FOREIGN KEY(college_id) REFERENCES colleges(id)
            );
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                is_super_admin INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS admin_college_access (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_user_id INTEGER NOT NULL,
                college_id INTEGER NOT NULL,
                FOREIGN KEY(admin_user_id) REFERENCES admin_users(id),
                FOREIGN KEY(college_id) REFERENCES colleges(id)
            );
            CREATE TABLE IF NOT EXISTS periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT NOT NULL,
                time_slot TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS timetable (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_id INTEGER,
                subject_id INTEGER,
                faculty_id INTEGER,
                classroom_id INTEGER,
                period_id INTEGER,
                FOREIGN KEY(section_id) REFERENCES sections(id),
                FOREIGN KEY(subject_id) REFERENCES subjects(id),
                FOREIGN KEY(faculty_id) REFERENCES faculty(id),
                FOREIGN KEY(classroom_id) REFERENCES classrooms(id),
                FOREIGN KEY(period_id) REFERENCES periods(id)
            );
        ''')
        dept_columns = {row['name'] for row in conn.execute('PRAGMA table_info(departments)')}
        if 'college_id' not in dept_columns:
            conn.execute('ALTER TABLE departments ADD COLUMN college_id INTEGER')
            conn.commit()

        section_columns = {row['name'] for row in conn.execute('PRAGMA table_info(sections)')}
        if 'college_id' not in section_columns:
            conn.execute('ALTER TABLE sections ADD COLUMN college_id INTEGER')
            conn.commit()

        faculty_columns = {row['name'] for row in conn.execute('PRAGMA table_info(faculty)')}
        if 'subject_id' not in faculty_columns:
            conn.execute('ALTER TABLE faculty ADD COLUMN subject_id INTEGER')
            conn.commit()

        classroom_columns = {row['name'] for row in conn.execute('PRAGMA table_info(classrooms)')}
        if 'college_id' not in classroom_columns:
            conn.execute('ALTER TABLE classrooms ADD COLUMN college_id INTEGER')
            conn.commit()

        # Seed default configuration if empty
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM colleges")
        if cursor.fetchone()[0] == 0:
            colleges = [
                ('SR University', 'SRU', 'Warangal, Telangana', 'https://placehold.co/160x160/1d4ed8/ffffff?text=SRU', 'https://www.sru.edu.in', 1),
                ('Kakatiya University', 'KU', 'Warangal, Telangana', 'https://placehold.co/160x160/0f766e/ffffff?text=KU', 'https://kakatiya.ac.in', 1),
                ('NIT Warangal', 'NITW', 'Warangal, Telangana', 'https://placehold.co/160x160/f59e0b/111827?text=NITW', 'https://www.nitw.ac.in', 1),
                ('Osmania University', 'OU', 'Hyderabad, Telangana', 'https://placehold.co/160x160/7c3aed/ffffff?text=OU', 'https://www.osmania.ac.in', 1),
                ('JNTU Hyderabad', 'JNTUH', 'Hyderabad, Telangana', 'https://placehold.co/160x160/ef4444/ffffff?text=JNTUH', 'https://jntuh.ac.in', 1),
            ]
            conn.executemany(
                "INSERT INTO colleges (name, short_name, location, logo_url, website, is_active) VALUES (?, ?, ?, ?, ?, ?)",
                colleges,
            )
            conn.commit()

        colleges = conn.execute("SELECT * FROM colleges ORDER BY id").fetchall()
        if colleges:
            college_ids = {row['name']: row['id'] for row in colleges}
            departments = conn.execute("SELECT * FROM departments").fetchall()
            if not departments:
                default_departments = [
                    ('Computer Science & Engineering', college_ids.get('SR University')),
                    ('Electronics & Communication Engineering', college_ids.get('SR University')),
                    ('Business Administration', college_ids.get('Kakatiya University')),
                    ('Mechanical Engineering', college_ids.get('NIT Warangal')),
                ]
                conn.executemany('INSERT INTO departments (name, college_id) VALUES (?, ?)', default_departments)
                conn.commit()
            else:
                for dept in departments:
                    if dept['college_id'] is None:
                        fallback_college_id = next((college['id'] for college in colleges), None)
                        if fallback_college_id is not None:
                            conn.execute('UPDATE departments SET college_id = ? WHERE id = ?', (fallback_college_id, dept['id']))
                conn.commit()

            section_rows = conn.execute('SELECT * FROM sections').fetchall()
            if not section_rows:
                dept_rows = conn.execute('SELECT * FROM departments ORDER BY id').fetchall()
                for dept in dept_rows:
                    college_id = dept['college_id']
                    if college_id is None:
                        college_id = next((college['id'] for college in colleges), None)
                    if college_id is not None:
                        conn.executemany(
                            'INSERT INTO sections (name, department_id, college_id) VALUES (?, ?, ?)',
                            [(f'{dept["name"]} - A', dept['id'], college_id), (f'{dept["name"]} - B', dept['id'], college_id)]
                        )
                conn.commit()
            else:
                for section in section_rows:
                    if section['college_id'] is None:
                        department = conn.execute('SELECT college_id FROM departments WHERE id = ?', (section['department_id'],)).fetchone()
                        fallback_college_id = department['college_id'] if department else next((college['id'] for college in colleges), None)
                        if fallback_college_id is not None:
                            conn.execute('UPDATE sections SET college_id = ? WHERE id = ?', (fallback_college_id, section['id']))
                conn.commit()

            classroom_rows = conn.execute('SELECT * FROM classrooms').fetchall()
            if not classroom_rows:
                sr_college_id = college_ids.get('SR University')
                if sr_college_id is not None:
                    conn.executemany(
                        'INSERT INTO classrooms (name, college_id, is_lab, capacity) VALUES (?, ?, ?, ?)',
                        [
                            ('Room 101', sr_college_id, 0, 60),
                            ('Room 202', sr_college_id, 0, 70),
                            ('Lab 1', sr_college_id, 1, 35),
                        ],
                    )
                    conn.commit()

            # Keep the requested departments available exactly once per college.
            for college in colleges:
                for alias, canonical in DEPARTMENT_ALIASES.items():
                    alias_rows = conn.execute(
                        'SELECT id FROM departments WHERE college_id = ? AND name = ?',
                        (college['id'], alias),
                    ).fetchall()
                    if not alias_rows:
                        continue
                    canonical_row = conn.execute(
                        'SELECT id FROM departments WHERE college_id = ? AND name = ? ORDER BY id LIMIT 1',
                        (college['id'], canonical),
                    ).fetchone()
                    if canonical_row:
                        for alias_row in alias_rows:
                            conn.execute('UPDATE sections SET department_id = ? WHERE department_id = ?', (canonical_row['id'], alias_row['id']))
                            conn.execute('UPDATE subjects SET department_id = ? WHERE department_id = ?', (canonical_row['id'], alias_row['id']))
                            conn.execute('UPDATE faculty SET department_id = ? WHERE department_id = ?', (canonical_row['id'], alias_row['id']))
                            conn.execute('DELETE FROM departments WHERE id = ?', (alias_row['id'],))
                    else:
                        conn.execute('UPDATE departments SET name = ? WHERE id = ?', (canonical, alias_rows[0]['id']))
                        for alias_row in alias_rows[1:]:
                            conn.execute('UPDATE sections SET department_id = ? WHERE department_id = ?', (alias_rows[0]['id'], alias_row['id']))
                            conn.execute('UPDATE subjects SET department_id = ? WHERE department_id = ?', (alias_rows[0]['id'], alias_row['id']))
                            conn.execute('UPDATE faculty SET department_id = ? WHERE department_id = ?', (alias_rows[0]['id'], alias_row['id']))
                            conn.execute('DELETE FROM departments WHERE id = ?', (alias_row['id'],))

                for department_name in REQUIRED_DEPARTMENTS:
                    existing = conn.execute(
                        'SELECT id FROM departments WHERE college_id = ? AND name = ? LIMIT 1',
                        (college['id'], department_name),
                    ).fetchone()
                    if not existing:
                        conn.execute(
                            'INSERT INTO departments (name, college_id) VALUES (?, ?)',
                            (department_name, college['id']),
                        )

                extra_departments = conn.execute(
                    'SELECT id FROM departments WHERE college_id = ? AND name NOT IN ({})'.format(
                        ', '.join('?' for _ in REQUIRED_DEPARTMENTS)
                    ),
                    (college['id'], *REQUIRED_DEPARTMENTS),
                ).fetchall()
                for extra_department in extra_departments:
                    department_id = extra_department['id']
                    conn.execute(
                        '''DELETE FROM timetable
                           WHERE section_id IN (SELECT id FROM sections WHERE department_id = ?)
                              OR subject_id IN (SELECT id FROM subjects WHERE department_id = ?)
                              OR faculty_id IN (SELECT id FROM faculty WHERE department_id = ?)''',
                        (department_id, department_id, department_id),
                    )
                    conn.execute('DELETE FROM sections WHERE department_id = ?', (department_id,))
                    conn.execute('DELETE FROM subjects WHERE department_id = ?', (department_id,))
                    conn.execute('DELETE FROM faculty WHERE department_id = ?', (department_id,))
                    conn.execute('DELETE FROM departments WHERE id = ?', (department_id,))

            for department in conn.execute('SELECT id, name, college_id FROM departments ORDER BY id').fetchall():
                section_code = SECTION_CODES[department['name']]
                sections = conn.execute(
                    'SELECT id FROM sections WHERE department_id = ? ORDER BY id',
                    (department['id'],),
                ).fetchall()
                for index in range(10):
                    section_name = f'{section_code}B{index + 1}'
                    if index < len(sections):
                        conn.execute(
                            'UPDATE sections SET name = ?, college_id = ? WHERE id = ?',
                            (section_name, department['college_id'], sections[index]['id']),
                        )
                    else:
                        conn.execute(
                            'INSERT INTO sections (name, department_id, college_id) VALUES (?, ?, ?)',
                            (section_name, department['id'], department['college_id']),
                        )
                for extra_section in sections[10:]:
                    conn.execute('DELETE FROM timetable WHERE section_id = ?', (extra_section['id'],))
                    conn.execute('DELETE FROM sections WHERE id = ?', (extra_section['id'],))
            conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_sections_department_name ON sections (department_id, name)')
            conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_departments_college_name ON departments (college_id, name)')

            for department in conn.execute('SELECT id, name, college_id FROM departments ORDER BY id').fetchall():
                college = conn.execute('SELECT short_name FROM colleges WHERE id = ?', (department['college_id'],)).fetchone()
                code = SECTION_CODES[department['name']]
                for subject_index, subject_name in enumerate(SUBJECT_TEMPLATES[department['name']]):
                    full_name = f'{college["short_name"]} {code} {subject_name}'
                    if not conn.execute('SELECT 1 FROM subjects WHERE department_id = ? AND name = ?', (department['id'], full_name)).fetchone():
                        conn.execute(
                            'INSERT INTO subjects (name, department_id, hours_per_week, is_lab) VALUES (?, ?, ?, ?)',
                            (full_name, department['id'], 3, 1 if subject_index == 1 and department['name'] in {'Computer Science and Engineering', 'Electronics and Electronics Engineering', 'Pharmacy'} else 0),
                        )
            conn.commit()
            conn.commit()

        admin_count = conn.execute('SELECT COUNT(*) FROM admin_users').fetchone()[0]
        if admin_count == 0:
            from werkzeug.security import generate_password_hash
            super_hash = generate_password_hash('admin123')
            conn.execute(
                'INSERT INTO admin_users (username, password_hash, full_name, is_super_admin) VALUES (?, ?, ?, ?)',
                ('superadmin', super_hash, 'Super Administrator', 1),
            )
            sr_college_id = conn.execute("SELECT id FROM colleges WHERE name = 'SR University'").fetchone()
            if sr_college_id:
                super_user_id = conn.execute("SELECT id FROM admin_users WHERE username = 'superadmin'").fetchone()[0]
                conn.execute(
                    'INSERT INTO admin_college_access (admin_user_id, college_id) VALUES (?, ?)',
                    (super_user_id, sr_college_id[0]),
                )
            conn.commit()

        cursor.execute("SELECT COUNT(*) FROM periods")
        if cursor.fetchone()[0] == 0:
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            slots = ['09:00 AM - 10:00 AM', '10:00 AM - 11:00 AM', '11:15 AM - 12:15 PM', '01:15 PM - 02:15 PM', '02:15 PM - 03:15 PM']
            for d in days:
                for s in slots:
                    conn.execute("INSERT INTO periods (day, time_slot) VALUES (?, ?)", (d, s))
            conn.commit()

init_db()

@app.route('/')
def index():
    return render_template('portal.html')

@app.route('/timetables')
def timetables():
    return render_template('public.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        configured_username = os.environ.get('ADMIN_USERNAME')
        configured_hash = os.environ.get('ADMIN_PASSWORD_HASH')

        db_user = None
        with get_db() as conn:
            db_user = conn.execute(
                'SELECT * FROM admin_users WHERE username = ?',
                (username,),
            ).fetchone()

        if db_user and check_password_hash(db_user['password_hash'], password):
            session.clear()
            session['is_admin'] = True
            session['admin_username'] = username
            session['admin_role'] = 'super' if db_user['is_super_admin'] else 'college'
            session['admin_user_id'] = db_user['id']
            if db_user['is_super_admin']:
                session['admin_college_id'] = None
            else:
                access_rows = conn.execute(
                    'SELECT college_id FROM admin_college_access WHERE admin_user_id = ?',
                    (db_user['id'],),
                ).fetchall()
                session['admin_college_id'] = access_rows[0]['college_id'] if access_rows else None
            return redirect(request.args.get('next') or url_for('admin_dashboard'))

        if (configured_username and configured_hash and
                username == configured_username and check_password_hash(configured_hash, password)):
            session.clear()
            session['is_admin'] = True
            session['admin_username'] = username
            session['admin_role'] = 'super'
            session['admin_user_id'] = None
            session['admin_college_id'] = None
            return redirect(request.args.get('next') or url_for('admin_dashboard'))
        error = 'Invalid administrator credentials.'

    return render_template('admin-login.html', error=error)

@app.post('/admin-logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template(
        'index.html',
        user_role=session.get('admin_role', 'college'),
        selected_college_id=session.get('admin_college_id')
    )

# --- Generic REST API helpers ---
def handle_crud(table, request):
    conn = get_db()
    cursor = conn.cursor()
    if not session.get('is_admin'):
        return jsonify({'status': 'error', 'message': 'Admin authentication required.'}), 401

    accessible_colleges = get_accessible_college_ids()
    is_admin_super = is_super_admin()

    def apply_college_filter(select_sql, params=()):
        if is_admin_super or not accessible_colleges:
            return cursor.execute(select_sql, params).fetchall()
        placeholders = ', '.join('?' for _ in accessible_colleges)
        return cursor.execute(f"{select_sql} WHERE {table}.college_id IN ({placeholders})", params + tuple(accessible_colleges)).fetchall()

    if request.method == 'GET':
        if table == 'colleges':
            rows = cursor.execute(
                'SELECT * FROM colleges WHERE id IN ({}) ORDER BY name'.format(', '.join('?' for _ in accessible_colleges)) if not is_admin_super and accessible_colleges else 'SELECT * FROM colleges ORDER BY name'
            , tuple(accessible_colleges) if not is_admin_super and accessible_colleges else ()).fetchall()
        elif table == 'departments':
            if is_admin_super:
                rows = cursor.execute('SELECT * FROM departments ORDER BY name').fetchall()
            else:
                rows = cursor.execute('SELECT * FROM departments WHERE college_id IN ({}) ORDER BY name'.format(', '.join('?' for _ in accessible_colleges)), tuple(accessible_colleges)).fetchall()
        elif table == 'sections':
            if is_admin_super:
                rows = cursor.execute('SELECT * FROM sections ORDER BY name').fetchall()
            else:
                rows = cursor.execute('SELECT * FROM sections WHERE college_id IN ({}) ORDER BY name'.format(', '.join('?' for _ in accessible_colleges)), tuple(accessible_colleges)).fetchall()
        elif table == 'subjects':
            if is_admin_super:
                rows = cursor.execute('SELECT * FROM subjects ORDER BY name').fetchall()
            else:
                rows = cursor.execute('''
                    SELECT s.* FROM subjects s
                    JOIN departments d ON s.department_id = d.id
                    WHERE d.college_id IN ({})
                    ORDER BY s.name
                '''.format(', '.join('?' for _ in accessible_colleges)), tuple(accessible_colleges)).fetchall()
        elif table == 'faculty':
            if is_admin_super:
                rows = cursor.execute('SELECT * FROM faculty ORDER BY name').fetchall()
            else:
                rows = cursor.execute('''
                    SELECT f.* FROM faculty f
                    JOIN departments d ON f.department_id = d.id
                    WHERE d.college_id IN ({})
                    ORDER BY f.name
                '''.format(', '.join('?' for _ in accessible_colleges)), tuple(accessible_colleges)).fetchall()
        elif table == 'classrooms':
            if is_admin_super:
                rows = cursor.execute('SELECT * FROM classrooms ORDER BY name').fetchall()
            else:
                rows = cursor.execute('SELECT * FROM classrooms WHERE college_id IN ({}) ORDER BY name'.format(', '.join('?' for _ in accessible_colleges)), tuple(accessible_colleges)).fetchall()
        else:
            rows = cursor.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()
        return jsonify([dict(row) for row in rows])
    elif request.method == 'POST':
        data = request.json or {}
        if table == 'departments':
            department_name = str(data.get('name', '')).strip()
            college_id = data.get('college_id')
            duplicate = cursor.execute(
                'SELECT id FROM departments WHERE college_id = ? AND name = ?',
                (college_id, department_name),
            ).fetchone()
            if duplicate:
                return jsonify({'status': 'error', 'message': 'That department already exists for this college.'}), 409
        if table == 'admin_users':
            if not is_admin_super:
                return jsonify({'status': 'error', 'message': 'Only the super admin can manage user permissions.'}), 403
            password = data.get('password')
            if password:
                data['password_hash'] = generate_password_hash(password)
                data.pop('password', None)
            elif 'password_hash' not in data:
                return jsonify({'status': 'error', 'message': 'Password is required.'}), 400
        if table in {'admin_college_access'} and not is_admin_super:
            return jsonify({'status': 'error', 'message': 'Only the super admin can manage user permissions.'}), 403
        if not is_admin_super and table in {'colleges', 'departments', 'sections', 'classrooms'}:
            college_id = data.get('college_id')
            if table == 'colleges' and college_id is not None and college_id not in accessible_colleges:
                return jsonify({'status': 'error', 'message': 'This college is not allowed for your account.'}), 403
            if table in {'departments', 'sections', 'classrooms'} and college_id not in accessible_colleges:
                return jsonify({'status': 'error', 'message': 'You can only manage your assigned college.'}), 403
        keys = list(data.keys())
        values = list(data.values())
        cols = ", ".join(keys)
        placeholders = ", ".join(["?" for _ in keys])
        cursor.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", values)
        conn.commit()
        return jsonify({"status": "success", "id": cursor.lastrowid})
    elif request.method == 'PUT':
        data = request.json or {}
        item_id = data.get('id')
        if table == 'departments':
            current = cursor.execute('SELECT * FROM departments WHERE id = ?', (item_id,)).fetchone()
            department_name = str(data.get('name', current['name'] if current else '')).strip()
            college_id = data.get('college_id', current['college_id'] if current else None)
            duplicate = cursor.execute(
                'SELECT id FROM departments WHERE college_id = ? AND name = ? AND id != ?',
                (college_id, department_name, item_id),
            ).fetchone()
            if duplicate:
                return jsonify({'status': 'error', 'message': 'That department already exists for this college.'}), 409
        if table == 'admin_users':
            if not is_admin_super:
                return jsonify({'status': 'error', 'message': 'Only the super admin can manage user permissions.'}), 403
            password = data.get('password')
            if password:
                data['password_hash'] = generate_password_hash(password)
                data.pop('password', None)
        if table in {'admin_college_access'} and not is_admin_super:
            return jsonify({'status': 'error', 'message': 'Only the super admin can manage user permissions.'}), 403
        if not is_admin_super and table in {'colleges', 'departments', 'sections', 'classrooms'}:
            current = cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
            if not current:
                return jsonify({'status': 'error', 'message': 'Record not found.'}), 404
            if table == 'colleges' and current['id'] not in accessible_colleges:
                return jsonify({'status': 'error', 'message': 'This college is not allowed for your account.'}), 403
            if table == 'departments' and current['college_id'] not in accessible_colleges:
                return jsonify({'status': 'error', 'message': 'You can only manage your assigned college.'}), 403
            if table == 'sections' and current['college_id'] not in accessible_colleges:
                return jsonify({'status': 'error', 'message': 'You can only manage your assigned college.'}), 403
            if table == 'classrooms' and current['college_id'] not in accessible_colleges:
                return jsonify({'status': 'error', 'message': 'You can only manage your assigned college.'}), 403
        set_clause = ", ".join([f"{k} = ?" for k in data.keys() if k != 'id'])
        values = [v for k, v in data.items() if k != 'id'] + [item_id]
        cursor.execute(f"UPDATE {table} SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return jsonify({"status": "updated"})
    elif request.method == 'DELETE':
        item_id = request.args.get('id')
        if table in {'admin_users', 'admin_college_access'} and not is_admin_super:
            return jsonify({'status': 'error', 'message': 'Only the super admin can manage user permissions.'}), 403
        if not is_admin_super and table in {'colleges', 'departments', 'sections', 'classrooms'}:
            current = cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
            if not current:
                return jsonify({'status': 'error', 'message': 'Record not found.'}), 404
            if table == 'colleges' and current['id'] not in accessible_colleges:
                return jsonify({'status': 'error', 'message': 'This college is not allowed for your account.'}), 403
            if table == 'departments' and current['college_id'] not in accessible_colleges:
                return jsonify({'status': 'error', 'message': 'You can only manage your assigned college.'}), 403
            if table == 'sections' and current['college_id'] not in accessible_colleges:
                return jsonify({'status': 'error', 'message': 'You can only manage your assigned college.'}), 403
            if table == 'classrooms' and current['college_id'] not in accessible_colleges:
                return jsonify({'status': 'error', 'message': 'You can only manage your assigned college.'}), 403
        cursor.execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
        conn.commit()
        return jsonify({"status": "deleted"})

@app.route('/api/departments', methods=['GET', 'POST', 'PUT', 'DELETE'])
@admin_required
def manage_departments(): return handle_crud('departments', request)

@app.route('/api/sections', methods=['GET', 'POST', 'PUT', 'DELETE'])
@admin_required
def manage_sections(): return handle_crud('sections', request)

@app.route('/api/subjects', methods=['GET', 'POST', 'PUT', 'DELETE'])
@admin_required
def manage_subjects(): return handle_crud('subjects', request)

@app.route('/api/faculty', methods=['GET', 'POST', 'PUT', 'DELETE'])
@admin_required
def manage_faculty(): return handle_crud('faculty', request)

@app.route('/api/classrooms', methods=['GET', 'POST', 'PUT', 'DELETE'])
@admin_required
def manage_classrooms(): return handle_crud('classrooms', request)

@app.route('/api/periods', methods=['GET'])
def get_periods(): return handle_crud('periods', request)

@app.route('/api/admin-users', methods=['GET', 'POST', 'PUT', 'DELETE'])
@admin_required
def manage_admin_users():
    if not is_super_admin():
        return jsonify({'status': 'error', 'message': 'Only the super admin can manage admin users.'}), 403
    return handle_crud('admin_users', request)

@app.route('/api/admin-college-access', methods=['GET', 'POST', 'PUT', 'DELETE'])
@admin_required
def manage_admin_college_access():
    if not is_super_admin():
        return jsonify({'status': 'error', 'message': 'Only the super admin can manage college access.'}), 403
    return handle_crud('admin_college_access', request)

@app.route('/api/colleges', methods=['GET', 'POST', 'PUT', 'DELETE'])
@admin_required
def manage_colleges(): return handle_crud('colleges', request)

@app.route('/api/timetable', methods=['GET'])
def get_timetable():
    conn = get_db()
    query = '''
        SELECT t.id, s.name as section_name, s.id as section_id, s.college_id as college_id,
               sub.name as subject_name, sub.id as subject_id, sub.is_lab,
               f.name as faculty_name, f.id as faculty_id,
               c.name as classroom_name, c.id as classroom_id,
               p.day, p.time_slot, p.id as period_id
        FROM timetable t
        JOIN sections s ON t.section_id = s.id
        JOIN subjects sub ON t.subject_id = sub.id
        JOIN faculty f ON t.faculty_id = f.id
        JOIN classrooms c ON t.classroom_id = c.id
        JOIN periods p ON t.period_id = p.id
    '''
    rows = conn.execute(query).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/public-timetable', methods=['GET'])
def get_public_timetable():
    conn = get_db()
    colleges = [dict(row) for row in conn.execute('SELECT * FROM colleges ORDER BY name')]
    departments = [dict(row) for row in conn.execute('SELECT id, name, college_id FROM departments ORDER BY name')]
    sections = [dict(row) for row in conn.execute('SELECT id, name, department_id, college_id FROM sections ORDER BY name')]
    faculty = [dict(row) for row in conn.execute('SELECT id, name FROM faculty ORDER BY name')]
    periods = [dict(row) for row in conn.execute('SELECT id, day, time_slot FROM periods ORDER BY id')]
    timetable = [dict(row) for row in conn.execute('''
        SELECT t.id, s.id AS section_id, s.name AS section_name,
               s.college_id AS college_id, s.department_id, sub.name AS subject_name,
               f.id AS faculty_id, f.name AS faculty_name,
               c.name AS classroom_name, p.day, p.time_slot
        FROM timetable t
        JOIN sections s ON t.section_id = s.id
        JOIN subjects sub ON t.subject_id = sub.id
        JOIN faculty f ON t.faculty_id = f.id
        JOIN classrooms c ON t.classroom_id = c.id
        JOIN periods p ON t.period_id = p.id
        ORDER BY p.id, s.name
    ''')]
    return jsonify({
        'colleges': colleges,
        'departments': departments,
        'sections': sections,
        'faculty': faculty,
        'periods': periods,
        'timetable': timetable,
    })

# --- AI Constraint-Satisfaction Optimization Engine ---
@app.route('/api/generate-ai-timetable', methods=['POST'])
@admin_required
def generate_ai_timetable():
    conn = get_db()
    cursor = conn.cursor()
    accessible_colleges = get_accessible_college_ids()
    if not accessible_colleges:
        return jsonify({'status': 'error', 'message': 'No college is assigned to this administrator.'}), 403
    college_placeholders = ', '.join('?' for _ in accessible_colleges)
    
    sections = cursor.execute(f"SELECT * FROM sections WHERE college_id IN ({college_placeholders})", accessible_colleges).fetchall()
    subjects = cursor.execute(f"SELECT s.* FROM subjects s JOIN departments d ON d.id = s.department_id WHERE d.college_id IN ({college_placeholders})", accessible_colleges).fetchall()
    faculty = cursor.execute(f"SELECT f.* FROM faculty f JOIN departments d ON d.id = f.department_id WHERE d.college_id IN ({college_placeholders})", accessible_colleges).fetchall()
    classrooms = cursor.execute(f"SELECT * FROM classrooms WHERE college_id IN ({college_placeholders})", accessible_colleges).fetchall()
    periods = cursor.execute("SELECT * FROM periods").fetchall()

    if not sections or not subjects or not faculty or not classrooms:
        return jsonify({"status": "error", "message": "Incomplete data! Add departments, subjects, faculty, and classrooms first."}), 400

    # Clear existing schedule
    cursor.execute(f"DELETE FROM timetable WHERE section_id IN (SELECT id FROM sections WHERE college_id IN ({college_placeholders}))", accessible_colleges)
    conn.commit()

    scheduled_count = 0
    conflicts_detected = 0
    assigned_slots = set() # Track (faculty_id, period_id) and (classroom_id, period_id) and (section_id, period_id)

    # Build work requirements queue
    allocation_queue = []
    for sec in sections:
        sec_subs = [sub for sub in subjects if sub['department_id'] == sec['department_id']]
        for sub in sec_subs:
            for _ in range(sub['hours_per_week']):
                allocation_queue.append((sec, sub))

    random.shuffle(allocation_queue)

    for sec, sub in allocation_queue:
        # Find matching faculty in the same department
        available_facs = [f for f in faculty if f['department_id'] == sec['department_id'] and f['subject_id'] == sub['id']]
        if not available_facs:
            available_facs = [f for f in faculty if f['department_id'] == sec['department_id'] and f['subject_id'] is None]
        if not available_facs:
            available_facs = [f for f in faculty if f['department_id'] == sec['department_id']]
        if not available_facs:
            available_facs = faculty # Fallback
        fac = random.choice(available_facs)

        # Find matching room (Lab vs Normal Classroom)
        matching_rooms = [c for c in classrooms if c['college_id'] == sec['college_id'] and c['is_lab'] == sub['is_lab']]
        if not matching_rooms:
            matching_rooms = [c for c in classrooms if c['college_id'] == sec['college_id']]
        room = random.choice(matching_rooms)

        # Find an open period avoiding conflicts
        valid_periods = []
        for p in periods:
            if (fac['id'], p['id']) not in assigned_slots and \
               (room['id'], p['id']) not in assigned_slots and \
               (sec['id'], p['id']) not in assigned_slots:
                valid_periods.append(p)

        if valid_periods:
            chosen_period = random.choice(valid_periods)
            assigned_slots.add((fac['id'], chosen_period['id']))
            assigned_slots.add((room['id'], chosen_period['id']))
            assigned_slots.add((sec['id'], chosen_period['id']))

            cursor.execute('''
                INSERT INTO timetable (section_id, subject_id, faculty_id, classroom_id, period_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (sec['id'], sub['id'], fac['id'], room['id'], chosen_period['id']))
            scheduled_count += 1
        else:
            conflicts_detected += 1

    conn.commit()

    # Calculate optimization score
    total_requested = len(allocation_queue)
    score = int((scheduled_count / total_requested) * 100) if total_requested > 0 else 100

    suggestions = []
    if conflicts_detected > 0:
        suggestions.append(f"Detected {conflicts_detected} unassigned lectures due to tight resource contention. Consider adding more Classrooms or Faculty members.")
    else:
        suggestions.append("All constraints successfully resolved with optimal room and faculty distribution!")

    return jsonify({
        "status": "success",
        "score": score,
        "scheduled_count": scheduled_count,
        "conflicts_detected": conflicts_detected,
        "colleges_generated": len({section['college_id'] for section in sections}),
        "suggestions": suggestions
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)