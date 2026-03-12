"""SQLite connection management."""
import sqlite3
import os
from contextlib import contextmanager
from config import DB_PATH


def init_db():
    """Create tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    schema = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema) as f:
        sql = f.read()
    with get_db() as conn:
        conn.executescript(sql)


@contextmanager
def get_db():
    """Yield a SQLite connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
