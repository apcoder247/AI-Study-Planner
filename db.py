import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "study_planner.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#4F46E5',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                exam_date TEXT NOT NULL,
                difficulty INTEGER NOT NULL DEFAULT 3,
                confidence INTEGER NOT NULL DEFAULT 50,
                importance INTEGER NOT NULL DEFAULT 3,
                estimated_minutes INTEGER NOT NULL DEFAULT 60,
                completed_minutes INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Pending',
                FOREIGN KEY(subject_id) REFERENCES subjects(id)
            );

            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                session_date TEXT NOT NULL,
                minutes INTEGER NOT NULL,
                FOREIGN KEY(topic_id) REFERENCES topics(id)
            );
            """
        )


def add_subject(name, color):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subjects(name, color, created_at) VALUES (?, ?, ?)",
            (name.strip(), color, datetime.now().isoformat()),
        )


def get_subjects():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM subjects ORDER BY name").fetchall()


def add_topic(subject_id, name, exam_date, difficulty, confidence, importance, estimated_minutes):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO topics(subject_id, name, exam_date, difficulty, confidence,
                               importance, estimated_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (subject_id, name.strip(), exam_date.isoformat(), difficulty, confidence, importance, estimated_minutes),
        )


def get_topics():
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT t.*, s.name AS subject_name, s.color AS subject_color
            FROM topics t JOIN subjects s ON t.subject_id = s.id
            ORDER BY t.exam_date, t.name
            """
        ).fetchall()


def update_topic_progress(topic_id, minutes):
    with get_conn() as conn:
        row = conn.execute("SELECT estimated_minutes FROM topics WHERE id=?", (topic_id,)).fetchone()
        if not row:
            return
        new_minutes = max(0, minutes)
        status = "Completed" if new_minutes >= row["estimated_minutes"] else "Pending"
        conn.execute(
            "UPDATE topics SET completed_minutes=?, status=? WHERE id=?",
            (new_minutes, status, topic_id),
        )


def add_session(topic_id, session_date, minutes):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO study_sessions(topic_id, session_date, minutes) VALUES (?, ?, ?)",
            (topic_id, session_date.isoformat(), minutes),
        )
        row = conn.execute("SELECT completed_minutes, estimated_minutes FROM topics WHERE id=?", (topic_id,)).fetchone()
        completed = row["completed_minutes"] + minutes
        status = "Completed" if completed >= row["estimated_minutes"] else "Pending"
        conn.execute("UPDATE topics SET completed_minutes=?, status=? WHERE id=?", (completed, status, topic_id))


def get_sessions():
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT ss.*, t.name AS topic_name, s.name AS subject_name
            FROM study_sessions ss
            JOIN topics t ON ss.topic_id=t.id
            JOIN subjects s ON t.subject_id=s.id
            ORDER BY ss.session_date DESC
            """
        ).fetchall()
