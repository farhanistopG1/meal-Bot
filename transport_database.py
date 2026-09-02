"""PostgreSQL repository for MealBot transport state."""

from __future__ import annotations

from database import get_connection


def find_telegram_home_link(
    chat_id: int,
):
    """Find the active Home linked to a Telegram chat."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    home_id,
                    provider,
                    purpose,
                    external_destination_id,
                    status
                FROM transport_endpoints
                WHERE provider = %s
                  AND external_destination_id = %s
                  AND status = %s
                LIMIT 1
                """,
                (
                    "telegram",
                    str(chat_id),
                    "Active",
                ),
            )

            return cursor.fetchone()

def create_telegram_home_link(
    home_id,
    chat_id: int,
):
    """Create an active Telegram transport endpoint for a Home."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO transport_endpoints (
                    home_id,
                    provider,
                    purpose,
                    external_destination_id,
                    status
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    home_id,
                    "telegram",
                    "resident_poll",
                    str(chat_id),
                    "Active",
                ),
            )

            return cursor.fetchone()
