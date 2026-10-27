import sqlite3
import pytest
from examples.vulnerable_app.engine import DynamicQueryEngine

def test_sql_injection_bypass(tmp_path):
    db_file = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("CREATE TABLE transactions (id INTEGER, reference_id TEXT, IsActive INTEGER)")
    c.execute("INSERT INTO transactions VALUES (1, 'REF-100', 1)")
    c.execute("INSERT INTO transactions VALUES (2, 'REF-200', 1)")
    conn.commit()
    conn.close()

    engine = DynamicQueryEngine(db_file)
    
    # Vulnerability test: raw SQL injection should fail if properly parameterized
    injection = "1=1 OR reference_id = 'REF-100'"
    engine.stage_clause(injection)
    results = engine.dispatch()
    
    # If safe/parameterized, it shouldn't return all rows (len should be <= 1)
    assert len(results) <= 1, "Vulnerable to raw string SQL injection!"
