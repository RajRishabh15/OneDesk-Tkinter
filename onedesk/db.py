"""MySQL configuration, pooled connections, transactions, and health checks.

Configuration is read from process environment variables first, then from the
project-root ``.env.local`` file. Secrets are never included in diagnostics.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
import threading
from typing import Iterator


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env.local"
POOL_SIZE = 5
CONNECT_TIMEOUT_SECONDS = 5

_ENV_KEYS = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
_pool = None
_pool_lock = threading.RLock()


class DatabaseConfigurationError(ValueError):
    """Raised when required database configuration is absent or invalid."""


class DatabaseDriverError(RuntimeError):
    """Raised when mysql-connector-python is not installed."""


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str

    def connector_options(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "connection_timeout": CONNECT_TIMEOUT_SECONDS,
            "autocommit": False,
        }


@dataclass(frozen=True)
class HealthCheckResult:
    ok: bool
    status: str
    database: str = ""
    version: str = ""
    message: str = ""


def _read_env_file(path: Path = ENV_FILE) -> dict[str, str]:
    """Read simple KEY=VALUE entries without requiring a dotenv dependency."""
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return values
    except OSError as exc:
        raise DatabaseConfigurationError("Could not read .env.local.") from exc

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or key not in _ENV_KEYS:
            raise DatabaseConfigurationError(
                f"Invalid .env.local entry on line {line_number}; expected a supported DB_* KEY=VALUE entry."
            )
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '\"'):
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        values[key] = value
    return values


def load_config() -> DatabaseConfig:
    """Load DB_* settings, with process environment taking precedence."""
    file_values = _read_env_file()

    def setting(key: str, default: str = "") -> str:
        return os.environ.get(key, file_values.get(key, default)).strip()

    host = setting("DB_HOST", "localhost")
    database = setting("DB_NAME", "onedesk")
    user = setting("DB_USER")
    password = setting("DB_PASSWORD")
    raw_port = setting("DB_PORT", "3306")

    if not host:
        raise DatabaseConfigurationError("DB_HOST must not be empty.")
    if not database:
        raise DatabaseConfigurationError("DB_NAME must not be empty.")
    if not user:
        raise DatabaseConfigurationError("DB_USER is required; set it in the environment or project-root .env.local.")
    if not password:
        raise DatabaseConfigurationError("DB_PASSWORD is required; set it in the environment or project-root .env.local.")
    try:
        port = int(raw_port)
    except (TypeError, ValueError) as exc:
        raise DatabaseConfigurationError("DB_PORT must be an integer from 1 to 65535.") from exc
    if not 1 <= port <= 65535:
        raise DatabaseConfigurationError("DB_PORT must be an integer from 1 to 65535.")

    return DatabaseConfig(host, port, database, user, password)


def _connector():
    try:
        import mysql.connector
        from mysql.connector import pooling
    except ImportError as exc:
        raise DatabaseDriverError(
            "mysql-connector-python is not installed; install the project requirements."
        ) from exc
    return mysql.connector, pooling


def get_pool():
    """Return the lazily initialized, reusable MySQL connection pool."""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _, pooling = _connector()
                config = load_config()
                _pool = pooling.MySQLConnectionPool(
                    pool_name="onedesk_pool",
                    pool_size=POOL_SIZE,
                    pool_reset_session=True,
                    **config.connector_options(),
                )
    return _pool


@contextmanager
def connection() -> Iterator:
    """Borrow a connection and always return it to the pool.

    This context does not commit. Use :func:`transaction` for writes.
    """
    conn = get_pool().get_connection()
    try:
        yield conn
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    else:
        if getattr(conn, "in_transaction", False):
            conn.rollback()
    finally:
        conn.close()


@contextmanager
def transaction() -> Iterator:
    """Borrow a connection, committing on success and rolling back on error."""
    with connection() as conn:
        yield conn
        conn.commit()


def query(sql: str, params=None, *, fetch: bool = True):
    """Execute SQL; return list[dict] when fetching, preserving the legacy API."""
    if fetch:
        with connection() as conn:
            cur = conn.cursor(dictionary=True)
            try:
                cur.execute(sql, params or {})
                return cur.fetchall()
            finally:
                cur.close()

    with transaction() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params or {})
        finally:
            cur.close()
    return None


def execute(sql: str, params=None) -> None:
    """Run and commit one INSERT, UPDATE, or DELETE statement."""
    query(sql, params, fetch=False)


def _diagnostic_status(exc: Exception) -> tuple[str, str]:
    errno = getattr(exc, "errno", None)
    if errno in (1044, 1045):
        return "authentication_failed", "MySQL rejected the configured user or its permissions."
    if errno == 1049:
        return "database_not_found", "The configured database does not exist or is not accessible."
    if errno in (2002, 2003, 2005, 2006, 2013):
        return "server_unavailable", "Could not reach the MySQL server; check host, port, and server status."
    return "connection_failed", "The MySQL connection or health check failed. See the exception type for details."


def health_check() -> HealthCheckResult:
    """Check the DB connection and return a safe status, selected DB, and version."""
    try:
        config = load_config()
    except DatabaseConfigurationError as exc:
        return HealthCheckResult(False, "missing_configuration", message=str(exc))

    try:
        with connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("SELECT 1")
                if cur.fetchone()[0] != 1:
                    return HealthCheckResult(False, "connection_failed", message="SELECT 1 returned an unexpected result.")
                cur.execute("SELECT DATABASE(), VERSION()")
                database, version = cur.fetchone()
            finally:
                cur.close()
        return HealthCheckResult(True, "ok", database or config.database, version or "", "Connection successful.")
    except DatabaseDriverError as exc:
        return HealthCheckResult(False, "driver_missing", message=str(exc))
    except Exception as exc:
        status, message = _diagnostic_status(exc)
        return HealthCheckResult(False, status, message=message)


def is_available() -> bool:
    """Backward-compatible availability check used by auth.py."""
    return health_check().ok


def close_pool() -> None:
    """Release the pool reference after all borrowed connections are returned.

    Connector/Python has no public pool-wide close operation. Each borrowed
    connection is returned with ``close()``; dropping the pool at process
    shutdown lets its idle connections be reclaimed by Python.
    """
    global _pool
    with _pool_lock:
        _pool = None
