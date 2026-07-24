from __future__ import annotations

from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT.body import Resident
from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT import database as home_database
from DCD.Project_MEALBOT.D2_MEAL_PLANNING.d2business_obr import MealPreference
from DCD.Project_MEALBOT.D2_MEAL_PLANNING import database as meal_preference_database


def configure_meal_preference(
    resident_phone: str,
    fav_meals: list[str],
    protein_preference: str,
    spice_preference: str,
) -> MealPreference:
    """Coordinate creation of a resident's validated meal preference."""

    resident = home_database.find_resident_by_phone(resident_phone)

    if resident is None:
        raise LookupError("Resident was not found.")

    meal_preference = MealPreference(
        resident=resident,
        fav_meals=fav_meals,
        protein_preference=protein_preference,
        spice_preference=spice_preference,
    )
    meal_preference_database.save(meal_preference)

    return meal_preference
