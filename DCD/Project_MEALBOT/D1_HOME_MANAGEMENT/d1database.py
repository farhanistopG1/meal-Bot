"""PostgreSQL repository for D1 Home Management."""

from __future__ import annotations

from database import get_connection
from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT.d1business_obr import (
    Cook,
    Home,
    Resident,
)


def _home_from_row(row) -> Home:
    home = Home(row["name"])
    home.id = row["id"]
    home.status = row["status"]
    home.created_at = row["created_at"]
    return home


def _resident_from_row(row) -> Resident:
    resident = Resident(row["name"], row["phone"])
    resident.id = row["id"]
    resident.status = row["status"]
    resident.onboarded_at = row["onboarded_at"]
    return resident


def _cook_from_row(row) -> Cook:
    cook = Cook(row["name"], row["phone"])
    cook.id = row["id"]
    cook.status = row["status"]
    cook.assigned_at = row["assigned_at"]
    return cook


def _load_home(connection, home_id) -> Home | None:
    """Load a complete Home aggregate from PostgreSQL."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                name,
                status,
                created_at
            FROM homes
            WHERE id = %s
            """,
            (home_id,),
        )

        home_row = cursor.fetchone()

        if home_row is None:
            return None

        home = _home_from_row(home_row)

        cursor.execute(
            """
            SELECT
                id,
                home_id,
                name,
                phone,
                status,
                onboarded_at
            FROM residents
            WHERE home_id = %s
            ORDER BY onboarded_at
            """,
            (home_id,),
        )

        home.residents = [
            _resident_from_row(resident_row)
            for resident_row in cursor.fetchall()
        ]

        cursor.execute(
            """
            SELECT
                id,
                home_id,
                name,
                phone,
                status,
                assigned_at
            FROM cooks
            WHERE home_id = %s
            LIMIT 1
            """,
            (home_id,),
        )

        cook_row = cursor.fetchone()

        home.cook = (
            _cook_from_row(cook_row)
            if cook_row
            else None
        )

        return home


def save(home: Home) -> Home:
    """
    Persist a newly configured Home, its residents, and cook atomically.
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:

            if home.id is None:
                cursor.execute(
                    """
                    INSERT INTO homes (
                        name,
                        status,
                        created_at
                    )
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (
                        home.name,
                        home.status,
                        home.created_at,
                    ),
                )

                home.id = cursor.fetchone()["id"]

            for resident in home.residents:

                if resident.id is None:
                    cursor.execute(
                        """
                        INSERT INTO residents (
                            home_id,
                            name,
                            phone,
                            status,
                            onboarded_at
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            home.id,
                            resident.name,
                            resident.phone,
                            resident.status,
                            resident.onboarded_at,
                        ),
                    )

                    resident.id = cursor.fetchone()["id"]

            if home.cook is not None and home.cook.id is None:
                cursor.execute(
                    """
                    INSERT INTO cooks (
                        home_id,
                        name,
                        phone,
                        status,
                        assigned_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        home.id,
                        home.cook.name,
                        home.cook.phone,
                        home.cook.status,
                        home.cook.assigned_at,
                    ),
                )

                home.cook.id = cursor.fetchone()["id"]

    return home


def save_resident(
    home: Home,
    resident: Resident,
) -> Resident:
    """Persist a new Resident under an existing Home."""

    if home.id is None:
        raise ValueError(
            "Home must be saved before adding residents."
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO residents (
                    home_id,
                    name,
                    phone,
                    status,
                    onboarded_at
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    home.id,
                    resident.name,
                    resident.phone,
                    resident.status,
                    resident.onboarded_at,
                ),
            )

            resident.id = cursor.fetchone()["id"]

    return resident


def list_homes() -> list[Home]:
    """Return all persisted Home aggregates."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM homes
                ORDER BY created_at
                """
            )

            home_ids = [
                row["id"]
                for row in cursor.fetchall()
            ]

        return [
            _load_home(
                connection,
                home_id,
            )
            for home_id in home_ids
        ]


def find_home_by_id(
    home_id,
) -> Home | None:
    """Find a complete Home aggregate by PostgreSQL ID."""

    with get_connection() as connection:
        return _load_home(
            connection,
            home_id,
        )


def find_resident_by_id(
    resident_id,
) -> Resident | None:
    """Find a Resident by PostgreSQL ID."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    home_id,
                    name,
                    phone,
                    status,
                    onboarded_at
                FROM residents
                WHERE id = %s
                """,
                (resident_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return _resident_from_row(row)


def find_resident_by_phone(
    phone: str,
) -> Resident | None:
    """
    Find a Resident by phone number.

    Phone numbers are currently stored as exact strings.
    The supplied value is stripped but otherwise not normalized.
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    home_id,
                    name,
                    phone,
                    status,
                    onboarded_at
                FROM residents
                WHERE phone = %s
                ORDER BY onboarded_at
                LIMIT 1
                """,
                (phone.strip(),),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return _resident_from_row(row)


def find_home_by_resident_id(
    resident_id,
) -> Home | None:
    """
    Find the complete Home aggregate belonging to a Resident.

    D1 owns this relationship, so callers such as organs.py
    do not need direct database access.
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT home_id
                FROM residents
                WHERE id = %s
                """,
                (resident_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            home_id = row["home_id"]

        return _load_home(
            connection,
            home_id,
        )