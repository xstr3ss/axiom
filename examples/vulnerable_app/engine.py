import sqlite3

class DynamicQueryEngine:
    def __init__(self, db_path):
        self.db_path = db_path
        self._buffer = ""

    def stage_clause(self, compiled_string):
        self._buffer = compiled_string

    def dispatch(self, driver_name="execute"):
        if not self._buffer:
            return []
        
        base_query = f"SELECT id, reference_id FROM transactions WHERE IsActive = 1 AND {self._buffer}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        executor = getattr(cursor, driver_name)
        executor(base_query)
        
        results = cursor.fetchall()
        conn.close()
        return results
