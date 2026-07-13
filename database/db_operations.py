"""
db_operations.py
----------------
All CRUD (Create/Read/Update/Delete) helper functions live here.
Every other module (chatbot.py, safety_journal.py, etc.) imports from this
file instead of writing raw SQL -- keeps queries in one auditable place.
"""

import pandas as pd
from database.db_setup import get_connection


# ---------------------------------------------------------------------
# CHAT HISTORY
# ---------------------------------------------------------------------
def save_chat_message(role: str, message: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_history (role, message) VALUES (?, ?)", (role, message)
    )
    conn.commit()
    conn.close()


def get_chat_history(limit: int = 100):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM chat_history ORDER BY id ASC LIMIT ?", conn, params=(limit,)
    )
    conn.close()
    return df


def clear_chat_history():
    conn = get_connection()
    conn.execute("DELETE FROM chat_history")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# LOCATION SAFETY SCORES
# ---------------------------------------------------------------------
def save_location_score(location_name, time_of_day, safety_score, risk_level, factors, tips):
    conn = get_connection()
    conn.execute(
        """INSERT INTO location_scores
           (location_name, time_of_day, safety_score, risk_level, factors, tips)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (location_name, time_of_day, safety_score, risk_level, factors, tips),
    )
    conn.commit()
    conn.close()


def get_location_history(limit: int = 20):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM location_scores ORDER BY id DESC LIMIT ?", conn, params=(limit,)
    )
    conn.close()
    return df


# ---------------------------------------------------------------------
# SOS CONTACTS
# ---------------------------------------------------------------------
def add_contact(name, phone, relation):
    conn = get_connection()
    conn.execute(
        "INSERT INTO sos_contacts (name, phone, relation) VALUES (?, ?, ?)",
        (name, phone, relation),
    )
    conn.commit()
    conn.close()


def get_contacts():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM sos_contacts ORDER BY id DESC", conn)
    conn.close()
    return df


def delete_contact(contact_id):
    conn = get_connection()
    conn.execute("DELETE FROM sos_contacts WHERE id = ?", (contact_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# SOS MESSAGES
# ---------------------------------------------------------------------
def save_sos_message(situation, location_text, generated_message, urgency_level):
    conn = get_connection()
    conn.execute(
        """INSERT INTO sos_messages (situation, location_text, generated_message, urgency_level)
           VALUES (?, ?, ?, ?)""",
        (situation, location_text, generated_message, urgency_level),
    )
    conn.commit()
    conn.close()


def get_sos_history(limit: int = 20):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM sos_messages ORDER BY id DESC LIMIT ?", conn, params=(limit,)
    )
    conn.close()
    return df


# ---------------------------------------------------------------------
# SAFETY JOURNAL
# ---------------------------------------------------------------------
def add_journal_entry(entry_text, mood, ai_insight):
    conn = get_connection()
    conn.execute(
        "INSERT INTO journal_entries (entry_text, mood, ai_insight) VALUES (?, ?, ?)",
        (entry_text, mood, ai_insight),
    )
    conn.commit()
    conn.close()


def get_journal_entries(limit: int = 50):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM journal_entries ORDER BY id DESC LIMIT ?", conn, params=(limit,)
    )
    conn.close()
    return df


def delete_journal_entry(entry_id):
    conn = get_connection()
    conn.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
