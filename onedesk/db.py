"""
OneDesk DB - db.py
MySQL connection pool and query helpers.
Credentials are read from config.ini in the project root.
"""

import configparser
import os
import mysql.connector
from mysql.connector import pooling

_pool = None


def _cfg() -> dict:
    ini = configparser.ConfigParser()
    ini_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    )
    ini.read(ini_path)
    sec = ini['mysql']
    return {
        "host":     sec.get("host",     "localhost"),
        "port":     sec.getint("port",  3306),
        "user":     sec.get("user",     "root"),
        "password": sec.get("password", ""),
        "database": sec.get("database", "onedesk"),
    }


def get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="onedesk_pool", pool_size=5, **_cfg()
        )
    return _pool


def query(sql: str, params=None, *, fetch: bool = True):
    """Execute SQL. Returns list[dict] if fetch=True, else None."""
    conn = get_pool().get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or {})
        result = cur.fetchall() if fetch else None
        conn.commit()
        return result
    finally:
        cur.close()
        conn.close()


def execute(sql: str, params=None) -> None:
    """Run INSERT / UPDATE / DELETE."""
    query(sql, params, fetch=False)


def is_available() -> bool:
    """True if a MySQL connection can be established right now."""
    try:
        conn = mysql.connector.connect(**_cfg())
        conn.close()
        return True
    except Exception:
        return False
