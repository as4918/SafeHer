"""
db_setup.py
-----------
Creates the SQLite database and all tables SafeHer AI needs.
Run automatically on app startup (see app.py -> init_database()).

TABLES
------
1. chat_history      -> stores every message exchanged with the AI safety chatbot
2. location_scores   -> stores every location safety-score lookup a user makes
3. sos_contacts      -> the user's trusted emergency contacts
4. sos_messages      -> log of generated SOS messages (for the "history" view)
5. journal_entries   -> safety journal entries + AI-generated insight per entry
"""

import sqlite3
import os
from config import DB_PATH


def get_connection():
    """Return a new SQLite connection. Each Streamlit rerun gets its own
    short-lived connection -- simplest & safest pattern for SQLite + Streamlit."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_database():
    """Create all tables if they do not already exist. Safe to call every run."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS location_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT NOT NULL,
            time_of_day TEXT NOT NULL,
            safety_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            factors TEXT,
            tips TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sos_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            relation TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sos_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            situation TEXT NOT NULL,
            location_text TEXT,
            generated_message TEXT NOT NULL,
            urgency_level TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_text TEXT NOT NULL,
            mood TEXT,
            ai_insight TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
    """)

    conn.commit()
    conn.close()
