"""Read-only MySQL connectivity and server-version check for OneDesk."""

import sys

from onedesk import db


def main() -> int:
    try:
        result = db.health_check()
        if result.ok:
            print("Database connection: OK")
            print(f"Database: {result.database}")
            print(f"MySQL version: {result.version}")
            return 0

        print(f"Database connection: FAILED ({result.status})")
        print(result.message)
        return 1
    finally:
        db.close_pool()


if __name__ == "__main__":
    sys.exit(main())
