from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT.organs import configure_home
from DCD.Project_MEALBOT.D2_MEAL_PLANNING.business_workflow import (
    configure_meal_preference,
)


def create_home(
    home_name: str,
    resident_name: str,
    resident_number: str,
    cook_name: str,
    cook_number: str,
):
    return configure_home(
        home_name=home_name,
        resident_name=resident_name,
        resident_number=resident_number,
        cook_name=cook_name,
        cook_number=cook_number,
    )


def create_meal_preference(
    resident_phone: str,
    fav_meals: list[str],
    protein_preference: str,
    spice_preference: str,
):
    return configure_meal_preference(
        resident_phone=resident_phone,
        fav_meals=fav_meals,
        protein_preference=protein_preference,
        spice_preference=spice_preference,
    )

