"""Create the MealBot PostgreSQL skeleton from database/mealbot_schema.sql.

Usage:
    MEALBOT_DATABASE_URL='postgresql://user:password@host:5432/mealbot' \
        python scripts/create_postgres_schema.py
"""

from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    database_url = os.environ.get("MEALBOT_DATABASE_URL")
    if not database_url:
        raise SystemExit("MEALBOT_DATABASE_URL must be set before creating the schema.")

    try:
        import psycopg
    except ImportError as error:
        raise SystemExit("Install project dependencies first: pip install -r requirements.txt") from error

    schema_path = Path(__file__).resolve().parents[1] / "database" / "mealbot_schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")

    with psycopg.connect(database_url, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(schema_sql)

    print(f"MealBot schema created or verified from {schema_path}.")


if __name__ == "__main__":
    main()
