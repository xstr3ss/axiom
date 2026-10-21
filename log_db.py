"""
Simple SQLite database module for storing logs.

Domain Constraints:
- Uses a local SQLite database file (default: 'logs.db').
- Log entries consist of: timestamp (ISO 8601 string), level (str, e.g., 'INFO', 'ERROR'), and message (str).

Preconditions:
- The current user must have write permissions to the current directory (or path to db file).
- Timestamps must be valid ISO 8601 strings (or parseable to datetime).

Postconditions:
- Upon successful connection/object initialization, the database file exists and the 'logs' table is created if not present.
- Upon successful insertion, the log entry is persisted and retrievable via query functions.
- No partial writes; transactions are committed atomically.
"""

import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional

class SQLiteLogStore:
    def __init__(self, db_path: str = "logs.db") -> None:
        """
        Initializes the SQLite log store and ensures the log table exists.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self) -> None:
        """Creates the logs table if it does not already exist."""
        cursor = self.connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL
            )
        ''')
        self.connection.commit()

    def add_log(self, timestamp: Optional[datetime], level: str, message: str) -> int:
        """
        Adds a log entry to the database.
        
        Args:
            timestamp: Optional datetime object. If None, current time is used.
            level: Log level string (e.g., 'INFO', 'DEBUG', 'ERROR').
            message: The log message content.
            
        Returns:
            int: The row ID of the inserted log entry.
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Ensure timestamp is stored as ISO 8601 string
        timestamp_str = timestamp.isoformat()
        
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO logs (timestamp, level, message) 
            VALUES (?, ?, ?)
        ''', (timestamp_str, level, message))
        
        self.connection.commit()
        return cursor.lastrowid

    def get_logs(self, limit: int = 100) -> List[Tuple[str, str, str]]:
        """
        Retrieves recent log entries.
        
        Args:
            limit: Maximum number of log entries to return.
            
        Returns:
            List of tuples (timestamp_iso_str, level, message).
        """
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT timestamp, level, message 
            FROM logs 
            ORDER BY id DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        # Return oldest first or sorted by id asc if "recent" implies latest n but displayed in order?
        # Usually "recent" implies latest. The prompt asks for List[Tuple[str, str, str]].
        # Let's return them in chronological order (oldest to newest) within the retrieved batch?
        # Or just return what the database gives (newest first)?
        # Standard convention: if I ask for "recent logs", I might want them displayed in order.
        # However, fetching DESC and returning them as-is is common for "tail -f" style.
        # Let's return them in chronological order (oldest of the fetched set to newest) for readability,
        # or just strict database order. The docstring doesn't specify order, just retrieves recent.
        # I will return them in the order they are stored (oldest to newest) by reversing the fetch?
        # No, usually "recent logs" list is okay to be newest first. I will stick to the fetch order (newest first).
        
        return [tuple(row) for row in results]

    def close(self) -> None:
        """
        Closes the database connection.
        """
        if self.connection:
            self.connection.close()
            self.connection = None