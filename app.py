import sqlite3
import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'lifesaver_secret_key'
DB_NAME = 'lifesaver.db'
CONFIG_FILE = 'config.json'


# ── Database Helpers ─────────────────────────────────────────

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def get_current_week():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
        return config.get('current_week', 1)


def set_current_week(week_num):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({'current_week': int(week_num)}, f, indent=2)


# ── Safe Schema Migrations ───────────────────────────────────

def get_table_columns(conn, table_name):
    """Return set of column names for a table."""
    cursor = conn.execute(f'PRAGMA table_info({table_name})')
    return {row[1] for row in cursor.fetchall()}


def run_migrations():
    """Add missing columns at startup. Safe, idempotent, preserves data."""
    conn = get_db_connection()

    # daily_checkins: add 'evidence' column
    cols = get_table_columns(conn, 'daily_checkins')
    if 'evidence' not in cols:
        conn.execute('ALTER TABLE daily_checkins ADD COLUMN evidence TEXT DEFAULT ""')
        print('[MIGRATION] Added evidence column to daily_checkins')

    # evidence_logs: expand schema
    cols = get_table_columns(conn, 'evidence_logs')
    migrations = [
        ('week', 'INTEGER DEFAULT 1'),
        ('evidence_type', 'TEXT DEFAULT "other"'),
        ('title', 'TEXT DEFAULT ""'),
        ('project_name', 'TEXT DEFAULT ""'),
        ('proof_link', 'TEXT DEFAULT ""'),
        ('commit_ref', 'TEXT DEFAULT ""'),
        ('impact_level', 'TEXT DEFAULT "medium"'),
    ]
    for col_name, col_def in migrations:
        if col_name not in cols:
            conn.execute(f'ALTER TABLE evidence_logs ADD COLUMN {col_name} {col_def}')
            print(f'[MIGRATION] Added {col_name} column to evidence_logs')

    # daily_tasks: add 'status' column
    cols = get_table_columns(conn, 'daily_tasks')
    if 'status' not in cols:
        conn.execute('ALTER TABLE daily_tasks ADD COLUMN status TEXT DEFAULT "pending"')
        print('[MIGRATION] Added status column to daily_tasks')

    conn.commit()
    conn.close()
    print('[MIGRATION] All migrations complete.')


# ── Jinja Filters ────────────────────────────────────────────

@app.template_filter('from_json')
def from_json_filter(value):
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return value


# ── Encoding Fix ─────────────────────────────────────────────

@app.after_request
def set_utf8_charset(response):
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


# ── Context Processor (week selector needs current week) ─────

@app.context_processor
def inject_globals():
    return {'active_week': get_current_week()}


# ── ROUTES ───────────────────────────────────────────────────

# ── Dashboard ────────────────────────────────────────────────

@app.route('/')
def index():
    week_num = get_current_week()
    conn = get_db_connection()

    # Roadmap data
    week = conn.execute(
        'SELECT * FROM weeks WHERE week_number = ?', (week_num,)
    ).fetchone()
    phase = None
    if week:
        phase = conn.execute(
            'SELECT * FROM phases WHERE phase_number = ?',
            (week['phase_number'],)
        ).fetchone()

    # Real tracked stats
    today_date = datetime.now().strftime('%Y-%m-%d')
    total_checkins = conn.execute(
        'SELECT COUNT(*) FROM daily_checkins'
    ).fetchone()[0]
    today_checkin = conn.execute(
        'SELECT * FROM daily_checkins WHERE date = ?', (today_date,)
    ).fetchone()

    # Task completion for current week
    total_tasks = conn.execute(
        'SELECT COUNT(*) FROM daily_tasks WHERE week = ?', (week_num,)
    ).fetchone()[0]
    done_tasks = conn.execute(
        'SELECT COUNT(*) FROM daily_tasks WHERE week = ? AND status = "done"',
        (week_num,)
    ).fetchone()[0]
    in_progress_tasks = conn.execute(
        'SELECT COUNT(*) FROM daily_tasks WHERE week = ? AND status = "in_progress"',
        (week_num,)
    ).fetchone()[0]

    # Evidence count for current week
    evidence_count = conn.execute(
        'SELECT COUNT(*) FROM evidence_logs WHERE week = ?', (week_num,)
    ).fetchone()[0]

    # Latest check-in
    latest_checkin = conn.execute(
        'SELECT day_verdict, date FROM daily_checkins ORDER BY date DESC LIMIT 1'
    ).fetchone()

    # Latest weekly review
    latest_review = conn.execute(
        'SELECT week_verdict, week FROM weekly_reviews ORDER BY id DESC LIMIT 1'
    ).fetchone()

    conn.close()

    stats = {
        'total_checkins': total_checkins,
        'today_done': today_checkin is not None,
        'today_verdict': today_checkin['day_verdict'] if today_checkin else None,
        'total_tasks': total_tasks,
        'done_tasks': done_tasks,
        'in_progress_tasks': in_progress_tasks,
        'evidence_count': evidence_count,
        'latest_verdict': latest_checkin['day_verdict'] if latest_checkin else None,
        'latest_verdict_date': latest_checkin['date'] if latest_checkin else None,
        'latest_review_verdict': latest_review['week_verdict'] if latest_review else None,
        'latest_review_week': latest_review['week'] if latest_review else None,
    }

    return render_template(
        'index.html', week=week, phase=phase,
        week_num=week_num, today_date=today_date, stats=stats
    )


# ── Daily Check-in (PRG + upsert) ───────────────────────────

@app.route('/checkin', methods=('GET', 'POST'))
def checkin():
    today_date = datetime.now().strftime('%Y-%m-%d')

    if request.method == 'POST':
        built = request.form.get('built', '')
        learned = request.form.get('learned', '')
        blockers = request.form.get('blockers', '')
        evidence = request.form.get('evidence', '')
        distraction = request.form.get('distraction', '')
        deep_work_minutes = request.form.get('deep_work', 0)
        day_verdict = request.form.get('day_verdict', '')

        conn = get_db_connection()
        existing = conn.execute(
            'SELECT id FROM daily_checkins WHERE date = ?', (today_date,)
        ).fetchone()

        if existing:
            conn.execute(
                '''UPDATE daily_checkins
                   SET built=?, learned=?, blockers=?, evidence=?,
                       distraction=?, deep_work_minutes=?, day_verdict=?
                   WHERE date=?''',
                (built, learned, blockers, evidence,
                 distraction, deep_work_minutes, day_verdict, today_date)
            )
            flash('Check-in updated for today.')
        else:
            conn.execute(
                '''INSERT INTO daily_checkins
                   (date, built, learned, blockers, evidence,
                    distraction, deep_work_minutes, day_verdict)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (today_date, built, learned, blockers, evidence,
                 distraction, deep_work_minutes, day_verdict)
            )
            if not evidence or evidence.strip() == '':
                flash('Check-in saved. No evidence logged — a day without proof is a day wasted.')
            elif distraction.lower() in ('none', 'low', '') and day_verdict == 'strong':
                flash('STRONG DAY logged. High evidence, low distraction.')
            else:
                flash('Check-in saved successfully.')

        conn.commit()
        conn.close()
        return redirect(url_for('checkin'))

    # GET: load today's existing check-in to pre-populate form
    conn = get_db_connection()
    today_checkin = conn.execute(
        'SELECT * FROM daily_checkins WHERE date = ?', (today_date,)
    ).fetchone()
    conn.close()

    return render_template(
        'checkin.html', today_date=today_date, today_checkin=today_checkin
    )


# ── Roadmap (unchanged) ─────────────────────────────────────

@app.route('/roadmap')
def roadmap():
    week_num = get_current_week()
    conn = get_db_connection()
    week = conn.execute(
        'SELECT * FROM weeks WHERE week_number = ?', (week_num,)
    ).fetchone()
    phase = None
    if week:
        phase = conn.execute(
            'SELECT * FROM phases WHERE phase_number = ?',
            (week['phase_number'],)
        ).fetchone()
    conn.close()
    return render_template('roadmap.html', week=week, phase=phase, week_num=week_num)


# ── Tasks + Status Toggle ───────────────────────────────────

@app.route('/tasks')
def tasks():
    week_num = get_current_week()
    conn = get_db_connection()
    tasks_query = conn.execute(
        'SELECT * FROM daily_tasks WHERE week = ? ORDER BY day ASC',
        (week_num,)
    ).fetchall()
    conn.close()
    return render_template('tasks.html', tasks=tasks_query, week_num=week_num)


@app.route('/tasks/update_status', methods=['POST'])
def update_task_status():
    task_id = request.form.get('task_id')
    new_status = request.form.get('status')

    if new_status not in ('pending', 'in_progress', 'done'):
        flash('Invalid task status.')
        return redirect(url_for('tasks'))

    conn = get_db_connection()
    conn.execute(
        'UPDATE daily_tasks SET status = ? WHERE id = ?',
        (new_status, task_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('tasks'))


# ── Weekly Review (PRG) ──────────────────────────────────────

@app.route('/review', methods=('GET', 'POST'))
def review():
    week_num = get_current_week()

    if request.method == 'POST':
        shipped_work = request.form.get('shipped_work', '')
        incomplete_work = request.form.get('incomplete_work', '')
        biggest_distraction = request.form.get('biggest_distraction', '')
        week_verdict = request.form.get('week_verdict', '')
        next_week_correction = request.form.get('next_week_correction', '')

        conn = get_db_connection()
        conn.execute(
            '''INSERT INTO weekly_reviews
               (week, week_goal, shipped_work, incomplete_work,
                biggest_distraction, week_verdict, next_week_correction)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (week_num, '', shipped_work, incomplete_work,
             biggest_distraction, week_verdict, next_week_correction)
        )
        conn.commit()
        conn.close()
        flash('Weekly review saved successfully.')
        return redirect(url_for('review'))

    conn = get_db_connection()
    template = conn.execute(
        'SELECT * FROM weekly_review_templates WHERE week_number = ?',
        (week_num,)
    ).fetchone()
    existing_review = conn.execute(
        'SELECT * FROM weekly_reviews WHERE week = ? ORDER BY id DESC LIMIT 1',
        (week_num,)
    ).fetchone()
    conn.close()

    return render_template(
        'review.html', template=template,
        week_num=week_num, existing_review=existing_review
    )


# ── Evidence Logs ────────────────────────────────────────────

@app.route('/evidence', methods=('GET', 'POST'))
def evidence():
    week_num = get_current_week()

    if request.method == 'POST':
        today_date = datetime.now().strftime('%Y-%m-%d')
        conn = get_db_connection()
        conn.execute(
            '''INSERT INTO evidence_logs
               (date, week, evidence_type, title, description,
                project_name, proof_link, commit_ref, impact_level)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                today_date,
                week_num,
                request.form.get('evidence_type', 'other'),
                request.form.get('title', ''),
                request.form.get('description', ''),
                request.form.get('project_name', ''),
                request.form.get('proof_link', ''),
                request.form.get('commit_ref', ''),
                request.form.get('impact_level', 'medium'),
            )
        )
        conn.commit()
        conn.close()
        flash('Evidence logged successfully.')
        return redirect(url_for('evidence'))

    conn = get_db_connection()
    logs = conn.execute(
        'SELECT * FROM evidence_logs ORDER BY id DESC LIMIT 30'
    ).fetchall()
    conn.close()

    return render_template('evidence.html', logs=logs, week_num=week_num)


# ── History ──────────────────────────────────────────────────

@app.route('/history')
def history():
    conn = get_db_connection()
    checkins = conn.execute(
        'SELECT * FROM daily_checkins ORDER BY date DESC LIMIT 14'
    ).fetchall()
    evidence_logs = conn.execute(
        'SELECT * FROM evidence_logs ORDER BY id DESC LIMIT 20'
    ).fetchall()
    reviews = conn.execute(
        'SELECT * FROM weekly_reviews ORDER BY id DESC LIMIT 12'
    ).fetchall()
    conn.close()

    return render_template(
        'history.html',
        checkins=checkins, evidence_logs=evidence_logs, reviews=reviews
    )


# ── Week Navigation ─────────────────────────────────────────

@app.route('/set_week', methods=['POST'])
def set_week():
    week = request.form.get('week', 1, type=int)
    if 1 <= week <= 12:
        set_current_week(week)
        flash(f'Active week set to Week {week}.')
    else:
        flash('Invalid week number.')
    referrer = request.referrer or url_for('index')
    return redirect(referrer)


# ── Entry Point ──────────────────────────────────────────────

if __name__ == '__main__':
    run_migrations()
    app.run(debug=True, port=5000)
