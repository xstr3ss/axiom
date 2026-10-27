import sqlite3
import re

class DynamicQueryEngine:
    """
    A simple dynamic query engine that safely builds SQL queries using
    parameterized statements. Only simple equality clauses of the form
    `<column> = <value>` are allowed. Any clause that does not match this
    pattern is considered unsafe and results in an empty result set.
    """
    _simple_eq_pattern = re.compile(
        r"""^\s*
        (?P<column>[A-Za-z_][A-Za-z0-9_]*)      # column name
        \s*=\s*
        (?P<quote>['"]?)                        # optional opening quote
        (?P<value>.+?)                          # value (non-greedy)
        (?P=quote)                              # matching closing quote if opened
        \s*$""",
        re.VERBOSE,
    )

    def __init__(self, db_path):
        self.db_path = db_path
        self._buffer = ""

    def stage_clause(self, compiled_string: str):
        """Store the raw clause string for later processing."""
        self._buffer = compiled_string

    def dispatch(self, driver_name: str = "execute"):
        """
        Execute the staged clause safely. If the clause matches the allowed
        simple equality pattern, it is executed using a parameterized query.
        Otherwise, an empty list is returned to avoid SQL injection.
        """
        if not self._buffer:
            return []

        match = self._simple_eq_pattern.match(self._buffer)
        if not match:
            # Clause is not in the allowed safe format; treat as no results.
            return []

        column = match.group("column")
        value = match.group("value")

        # Build a parameterized query using the validated column name.
        base_query = (
            f"SELECT id, reference_id FROM transactions "
            f"WHERE IsActive = 1 AND {column} = ?"
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        executor = getattr(cursor, driver_name)
        executor(base_query, (value,))

        results = cursor.fetchall()
        conn.close()
        return results
