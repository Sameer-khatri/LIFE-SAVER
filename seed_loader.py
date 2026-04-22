import sqlite3
import json
import os

DB_NAME = 'lifesaver.db'

def reset_and_create_tables(cursor):
    tables = [
        "mission", "phases", "weeks", "daily_tasks", 
        "weekly_review_templates", "daily_checkins", 
        "evidence_logs", "weekly_reviews"
    ]
    
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    
    # 1. system_config / mission
    cursor.execute("""
        CREATE TABLE mission (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT,
            version TEXT,
            mission TEXT,
            identity TEXT
        )
    """)

    # 2. phases
    cursor.execute("""
        CREATE TABLE phases (
            phase_number INTEGER PRIMARY KEY,
            title TEXT,
            start_week INTEGER,
            end_week INTEGER,
            goal TEXT
        )
    """)

    # 3. weeks
    cursor.execute("""
        CREATE TABLE weeks (
            week_number INTEGER PRIMARY KEY,
            phase_number INTEGER,
            theme TEXT,
            goal TEXT,
            success_definition TEXT,
            rules TEXT,
            deliverables TEXT
        )
    """)

    # 4. daily_tasks
    cursor.execute("""
        CREATE TABLE daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week INTEGER,
            day INTEGER,
            title TEXT,
            main_goal TEXT,
            build_task TEXT,
            support_task TEXT,
            planned_output TEXT,
            evidence_required TEXT,
            anti_distraction_warning TEXT
        )
    """)

    # 5. weekly_review_templates
    cursor.execute("""
        CREATE TABLE weekly_review_templates (
            week_number INTEGER PRIMARY KEY,
            success_definition TEXT,
            bad_week_signals TEXT,
            strong_week_signals TEXT,
            deliverables TEXT
        )
    """)

    # 6. daily_checkins (Empty)
    cursor.execute("""
        CREATE TABLE daily_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            built TEXT,
            learned TEXT,
            blockers TEXT,
            distraction TEXT,
            deep_work_minutes INTEGER,
            day_verdict TEXT
        )
    """)

    # 7. evidence_logs (Empty)
    cursor.execute("""
        CREATE TABLE evidence_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            type TEXT,
            description TEXT
        )
    """)

    # 8. weekly_reviews (Empty)
    cursor.execute("""
        CREATE TABLE weekly_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week INTEGER,
            week_goal TEXT,
            shipped_work TEXT,
            incomplete_work TEXT,
            biggest_distraction TEXT,
            week_verdict TEXT,
            next_week_correction TEXT
        )
    """)

def load_data(cursor):
    # Load weeks_seed.json
    with open('weeks_seed.json', 'r', encoding='utf-8') as f:
        weeks_data = json.load(f)
        
        # Load Mission
        cursor.execute(
            "INSERT INTO mission (app_name, version, mission, identity) VALUES (?, ?, ?, ?)",
            (weeks_data.get("app_name"), weeks_data.get("version"), weeks_data.get("mission"), weeks_data.get("identity"))
        )

        # Load Phases
        for phase in weeks_data.get("phases", []):
            cursor.execute(
                "INSERT INTO phases (phase_number, title, start_week, end_week, goal) VALUES (?, ?, ?, ?, ?)",
                (phase.get("phase_number"), phase.get("title"), phase.get("start_week"), phase.get("end_week"), phase.get("goal"))
            )

        # Load Weeks
        for week in weeks_data.get("weeks", []):
            cursor.execute(
                "INSERT INTO weeks (week_number, phase_number, theme, goal, success_definition, rules, deliverables) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    week.get("week_number"), 
                    week.get("phase_number"), 
                    week.get("theme"), 
                    week.get("goal"),
                    json.dumps(week.get("success_definition", [])),
                    json.dumps(week.get("rules", [])),
                    json.dumps(week.get("deliverables", []))
                )
            )
            
    # Load daily_tasks_seed.json
    with open('daily_tasks_seed.json', 'r', encoding='utf-8') as f:
        daily_tasks_data = json.load(f)
        
        for task in daily_tasks_data.get("tasks", []):
            cursor.execute(
                "INSERT INTO daily_tasks (week, day, title, main_goal, build_task, support_task, planned_output, evidence_required, anti_distraction_warning) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    task.get("week"), task.get("day"), task.get("title"), task.get("main_goal"),
                    json.dumps(task.get("build_task", [])),
                    json.dumps(task.get("support_task", [])),
                    json.dumps(task.get("planned_output", [])),
                    json.dumps(task.get("evidence_required", [])),
                    json.dumps(task.get("anti_distraction_warning", []))
                )
            )
            
    # Load weekly_review_templates.json
    with open('weekly_review_templates.json', 'r', encoding='utf-8') as f:
        templates_data = json.load(f)
        
        for template in templates_data.get("templates", []):
            cursor.execute(
                "INSERT INTO weekly_review_templates (week_number, success_definition, bad_week_signals, strong_week_signals, deliverables) VALUES (?, ?, ?, ?, ?)",
                (
                    template.get("week_number"),
                    json.dumps(template.get("success_definition", [])),
                    json.dumps(template.get("bad_week_signals", [])),
                    json.dumps(template.get("strong_week_signals", [])),
                    json.dumps(template.get("deliverables", []))
                )
            )

def print_row_counts(cursor):
    tables = [
        "mission", "phases", "weeks", "daily_tasks", 
        "weekly_review_templates", "daily_checkins", 
        "evidence_logs", "weekly_reviews"
    ]
    
    print("Database seeding completed.")
    print("-" * 30)
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Table '{table}': {count} rows")
    print("-" * 30)

def main():
    print(f"Connecting to {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("Dropping and re-creating tables...")
    reset_and_create_tables(cursor)
    
    print("Parsing JSON files and inserting data...")
    load_data(cursor)
    
    conn.commit()
    print_row_counts(cursor)
    
    conn.close()
    print("Done!")

if __name__ == "__main__":
    main()
