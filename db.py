"""
db.py — Database connection pool and cursor context manager.
Extracted from app.py as part of Flask Blueprint modularization.
"""
import os
import mysql.connector
import mysql.connector.pooling
from contextlib import contextmanager

DB_HOST = os.environ.get("READWISE_DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("READWISE_DB_PORT", "3306"))
DB_USER = os.environ.get("READWISE_DB_USER", "root")
DB_PASSWORD = os.environ.get("READWISE_DB_PASSWORD", "")
DB_NAME = os.environ.get("READWISE_DB_NAME", "readwise_db")

if not __import__("re").fullmatch(r"[A-Za-z0-9_]+", DB_NAME):
    raise RuntimeError("Invalid READWISE_DB_NAME")

_DB_POOL = None


def mysql_config(include_db=True):
    cfg = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "charset": "utf8mb4",
        "use_unicode": True,
    }
    if include_db:
        cfg["database"] = DB_NAME
    return cfg


def db_pool():
    global _DB_POOL
    if _DB_POOL is None:
        _DB_POOL = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="readwise_pool", pool_size=6, autocommit=False, **mysql_config(True)
        )
    return _DB_POOL


@contextmanager
def db_cursor(dictionary=False):
    conn = db_pool().get_connection()
    cur = conn.cursor(dictionary=dictionary)
    try:
        yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
