"""PostgreSQL repository for D2 meal preference versions."""

from __future__ import annotations

from database import get_connection

from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT import d1database
from DCD.Project_MEALBOT.D2_MEAL_PLANNING.d2business_obr import (
    MealPreference,
)


def save(meal_preference: MealPreference) -> MealPreference:
    """
    Persist a new MealPreference version for a Resident.

    The Resident row is locked for the duration of the transaction so that
    concurrent preference updates for the same Resident cannot calculate
    the same preference version.
    """

    resident_id = meal_preference.resident.id

    if resident_id is None:
        raise ValueError(
            "Resident must be saved before saving preferences."
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:

            # Lock the Resident row. This is the serialization point for
            # preference version creation for this Resident.
            cursor.execute(
                """
                SELECT id
                FROM residents
                WHERE id = %s
                FOR UPDATE
                """,
                (resident_id,),
            )

            resident_row = cursor.fetchone()

            if resident_row is None:
                raise LookupError(
                    "Resident does not exist."
                )

            # Now it is safe to determine the next version because another
            # preference update for this Resident cannot pass the lock above.
            cursor.execute(
                """
                SELECT COALESCE(MAX(version), 0) + 1 AS next_version
                FROM meal_preferences
                WHERE resident_id = %s
                """,
                (resident_id,),
            )

            version = cursor.fetchone()["next_version"]

            # Retire the previous current preference.
            cursor.execute(
                """
                UPDATE meal_preferences
                SET
                    is_current = FALSE,
                    superseded_at = now()
                WHERE resident_id = %s
                  AND is_current = TRUE
                """,
                (resident_id,),
            )

            # Create the new current preference.
            cursor.execute(
                """
                INSERT INTO meal_preferences (
                    resident_id,
                    version,
                    protein_preference,
                    spice_preference,
                    is_current
                )
                VALUES (%s, %s, %s, %s, TRUE)
                RETURNING id, created_at
                """,
                (
                    resident_id,
                    version,
                    meal_preference.protein_preference,
                    meal_preference.spice_preference,
                ),
            )

            row = cursor.fetchone()

            meal_preference.id = row["id"]
            meal_preference.version = version
            meal_preference.created_at = row["created_at"]

            # Persist the five favourite meals.
            for position, meal_name in enumerate(
                sorted(meal_preference.fav_meals),
                start=1,
            ):
                cursor.execute(
                    """
                    INSERT INTO meal_preference_items (
                        meal_preference_id,
                        meal_name,
                        position
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (
                        meal_preference.id,
                        meal_name,
                        position,
                    ),
                )

    return meal_preference


def list_meals() -> list[MealPreference]:
    """
    Return the current MealPreference for each Resident.

    Historical preference versions remain persisted in PostgreSQL but are
    not returned here because D3 requires each Resident's current preference.
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    resident_id,
                    version,
                    protein_preference,
                    spice_preference,
                    is_current,
                    created_at
                FROM meal_preferences
                WHERE is_current = TRUE
                ORDER BY created_at
                """
            )

            preference_rows = cursor.fetchall()

            preferences = []

            for row in preference_rows:

                resident = d1database.find_resident_by_id(
                    row["resident_id"]
                )

                if resident is None:
                    raise LookupError(
                        "A MealPreference references a Resident "
                        "that does not exist."
                    )

                cursor.execute(
                    """
                    SELECT meal_name
                    FROM meal_preference_items
                    WHERE meal_preference_id = %s
                    ORDER BY position
                    """,
                    (row["id"],),
                )

                meal_items = cursor.fetchall()

                preference = MealPreference(
                    resident,
                    [
                        item["meal_name"]
                        for item in meal_items
                    ],
                    row["protein_preference"],
                    row["spice_preference"],
                )

                preference.id = row["id"]
                preference.version = row["version"]
                preference.created_at = row["created_at"]

                preferences.append(preference)

            return preferences