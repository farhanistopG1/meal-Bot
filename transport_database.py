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

def find_active_home_telegram_chat_id(
    home_id,
):
    """Find the active Telegram chat ID linked to a Home."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT external_destination_id
                FROM transport_endpoints
                WHERE home_id = %s
                  AND provider = %s
                  AND purpose = %s
                  AND status = %s
                LIMIT 1
                """,
                (
                    home_id,
                    "telegram",
                    "resident_poll",
                    "Active",
                ),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return int(row["external_destination_id"])


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

def find_active_telegram_chats():
    """Return all active Telegram chat IDs linked to Homes."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT external_destination_id
                FROM transport_endpoints
                WHERE provider = %s
                  AND purpose = %s
                  AND status = %s
                """,
                (
                    "telegram",
                    "resident_poll",
                    "Active",
                ),
            )

            return [
                int(row["external_destination_id"])
                for row in cursor.fetchall()
            ]


def find_home_telegram_identities(home_id):
    """Return Telegram user IDs linked to Residents of a Home."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT rti.external_user_id
                FROM resident_transport_identities rti
                JOIN residents r
                  ON r.id = rti.resident_id
                WHERE r.home_id = %s
                  AND rti.provider = %s
                  AND rti.status = %s
                """,
                (
                    home_id,
                    "telegram",
                    "Active",
                ),
            )

            return [
                row["external_user_id"]
                for row in cursor.fetchall()
            ]

def create_resident_telegram_identity(
    resident_id,
    telegram_user_id: int,
):
    """Bind a Telegram user identity to a Resident."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO resident_transport_identities (
                    resident_id,
                    provider,
                    external_user_id,
                    status
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    resident_id,
                    "telegram",
                    str(telegram_user_id),
                    "Active",
                ),
            )
            return cursor.fetchone()

def create_poll_binding(home_id, daily_meal_poll_id, transport_endpoint_id, provider_poll_id, provider_message_id=None):
    """Create the external transport binding for a D3 meal poll."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO transport_poll_bindings (
                    home_id,
                    daily_meal_poll_id,
                    transport_endpoint_id,
                    provider_poll_id,
                    provider_message_id
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    home_id,
                    daily_meal_poll_id,
                    transport_endpoint_id,
                    provider_poll_id,
                    provider_message_id,
                ),
            )
            return cursor.fetchone()


def find_binding_by_daily_meal_poll(daily_meal_poll_id):
    """Find the external transport binding for a D3 meal poll."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM transport_poll_bindings
                WHERE daily_meal_poll_id = %s
                LIMIT 1
                """,
                (daily_meal_poll_id,),
            )
            return cursor.fetchone()

def find_binding_by_provider_poll_id(provider_poll_id):
    """Find the transport binding for an external Telegram poll."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM transport_poll_bindings
                WHERE provider_poll_id = %s
                LIMIT 1
                """,
                (provider_poll_id,),
            )
            return cursor.fetchone()


def close_poll_binding(daily_meal_poll_id):
    """Mark the external transport binding as closed."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE transport_poll_bindings
                SET closed_at = NOW()
                WHERE daily_meal_poll_id = %s
                  AND closed_at IS NULL
                RETURNING *
                """,
                (daily_meal_poll_id,),
            )
            return cursor.fetchone()


def find_active_home_telegram_endpoint(home_id):
    """Find the active Telegram transport endpoint for a Home."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    external_destination_id
                FROM transport_endpoints
                WHERE home_id = %s
                  AND provider = %s
                  AND purpose = %s
                  AND status = %s
                LIMIT 1
                """,
                (
                    home_id,
                    "telegram",
                    "resident_poll",
                    "Active",
                ),
            )
            return cursor.fetchone()


def find_resident_by_telegram_identity(telegram_user_id: int):
    """Find the Resident bound to a Telegram user identity."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT r.*
                FROM residents r
                JOIN resident_transport_identities rti
                  ON r.id = rti.resident_id
                WHERE rti.provider = %s
                  AND rti.external_user_id = %s
                  AND rti.status = %s
                LIMIT 1
                """,
                (
                    "telegram",
                    str(telegram_user_id),
                    "Active",
                ),
            )
            return cursor.fetchone()
