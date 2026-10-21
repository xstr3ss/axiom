import sqlite3
import os
from typing import List, Optional

DB_PATH = "logs.db"

def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_entries (
            entry_id INTEGER PRIMARY KEY,
            log_entry TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

def create_log_entry(entry_id: int, log_entry: str) -> None:
    """
    Create a log entry in the SQLite database.

    Parameters:
    entry_id (int): The unique identifier for the log entry.
    log_entry (str): The content of the log entry.

    Postconditions:
    - The log entry is successfully created in the SQLite database.
    """
    if not isinstance(entry_id, int):
        raise TypeError("entry_id must be an integer")
    if not isinstance(log_entry, str):
        raise TypeError("log_entry must be a string")
    
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO log_entries (entry_id, log_entry) VALUES (?, ?)", (entry_id, log_entry))
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("Log entry with this ID already exists")
    finally:
        conn.close()

def get_all_log_entries() -> List[str]:
    """
    Retrieve all log entries from the SQLite database.

    Parameters:
    None

    Postconditions:
    - Returns a list of all log entries stored in the SQLite database.
    Preconditions:
    - The SQLite database must contain at least one log entry.
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT log_entry FROM log_entries")
        rows = cursor.fetchall()
        if not rows:
            raise ValueError("Database must contain at least one log entry")
        return [row[0] for row in rows]
    finally:
        conn.close()

def update_log_entry(entry_id: int, new_entry: str) -> None:
    """
    Update an existing log entry in the SQLite database.

    Parameters:
    entry_id (int): The unique identifier of the log entry to be updated.
    new_entry (str): The updated content of the log entry.

    Postconditions:
    - The log entry with the specified ID is updated with the new content.
    Preconditions:
    - The SQLite database must contain a log entry with the specified ID.
    """
    if not isinstance(entry_id, int):
        raise TypeError("entry_id must be an integer")
    if not isinstance(new_entry, str):
        raise TypeError("new_entry must be a string")

    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM log_entries WHERE entry_id = ?", (entry_id,))
        if cursor.fetchone() is None:
            raise ValueError("Log entry with specified ID does not exist")
        
        cursor.execute("UPDATE log_entries SET log_entry = ? WHERE entry_id = ?", (new_entry, entry_id))
        conn.commit()
    finally:
        conn.close()

def delete_log_entry(entry_id: int) -> None:
    """
    Delete a log entry from the SQLite database.

    Parameters:
    entry_id (int): The unique identifier of the log entry to be deleted.

    Postconditions:
    - The log entry with the specified ID is removed from the SQLite database.
    Preconditions:
    - The SQLite database must contain a log entry with the specified ID.
    """
    if not isinstance(entry_id, int):
        raise TypeError("entry_id must be an integer")

    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM log_entries WHERE entry_id = ?", (entry_id,))
        if cursor.fetchone() is None:
            raise ValueError("Log entry with specified ID does not exist")
        
        cursor.execute("DELETE FROM log_entries WHERE entry_id = ?", (entry_id,))
        conn.commit()
    finally:
        conn.close()