"""Runtime orchestration layer for MealBot.

The runtime coordinates domain workflows and repositories.
It does not contain SQL or domain business rules.
"""

from __future__ import annotations

from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT import (
    d1database as home_database,
)
import transport_database
from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT.d1business_obr import (
    Resident,
)
from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT.d1business_workflow import (
    configure_home,
)
from DCD.Project_MEALBOT.D2_MEAL_PLANNING.d2business_workflow import (
    configure_meal_preference,
)
from DCD.Project_MEALBOT.D3_Daily_Meal_Coordination import (
    d3database,
)
from DCD.Project_MEALBOT.D3_Daily_Meal_Coordination.d3business_workflow import (
    close_daily_meal_poll,
    start_daily_meal_poll,
    submit_meal_vote,
)


def get_telegram_home_link(
    chat_id: int,
):
    """Resolve a Telegram chat to its linked MealBot Home."""

    if not isinstance(chat_id, int):
        raise ValueError("Telegram chat ID must be an integer.")

    return transport_database.find_telegram_home_link(
        chat_id
    )


def create_home(
    home_name: str,
    resident_name: str,
    resident_number: str,
    cook_name: str,
    cook_number: str,
    telegram_chat_id: int,
):
    """Create a Home and bind it to its Telegram group."""

    if not isinstance(telegram_chat_id, int):
        raise ValueError(
            "Telegram chat ID must be an integer."
        )

    home = configure_home(
        home_name=home_name,
        resident_name=resident_name,
        resident_number=resident_number,
        cook_name=cook_name,
        cook_number=cook_number,
    )

    transport_database.create_telegram_home_link(
        home_id=home.id,
        chat_id=telegram_chat_id,
    )

    return home


def create_meal_preference(
    resident_phone: str,
    fav_meals: list[str],
    protein_preference: str,
    spice_preference: str,
):
    """Create a resident's MealPreference through D2."""

    return configure_meal_preference(
        resident_phone=resident_phone,
        fav_meals=fav_meals,
        protein_preference=protein_preference,
        spice_preference=spice_preference,
    )


def _find_home_and_resident(
    resident_phone: str,
):
    """
    Resolve a resident and the Home they belong to.

    D1 owns resident persistence and the Resident → Home relationship.
    Runtime only coordinates the lookup.
    """

    if (
        not isinstance(resident_phone, str)
        or not resident_phone.strip()
    ):
        raise ValueError(
            "Resident phone is required."
        )

    normalized_phone = resident_phone.strip()

    resident = home_database.find_resident_by_phone(
        normalized_phone
    )

    if resident is None:
        raise LookupError(
            "Resident was not found."
        )

    home = home_database.find_home_by_resident_id(
        resident.id
    )

    if home is None:
        raise LookupError(
            "Resident's Home was not found."
        )

    return home, resident


def add_resident_to_home(
    anchor_resident_phone: str,
    resident_name: str,
    resident_number: str,
):
    """
    Add a Resident to the Home identified by an
    existing Resident.
    """

    home, _ = _find_home_and_resident(
        anchor_resident_phone
    )

    normalized_phone = resident_number.strip()

    if any(
        resident.phone == normalized_phone
        for resident in home.residents
    ):
        raise ValueError(
            "A resident with this phone number "
            "already belongs to the Home."
        )

    resident = Resident(
        resident_name,
        normalized_phone,
    )

    home.add_resident(
        resident
    )

    home_database.save_resident(
        home,
        resident,
    )

    return resident


def create_daily_meal_poll(
    anchor_resident_phone: str,
    meal_date=None,
):
    """
    Start an open D3 poll for the Home containing
    the anchor Resident.
    """

    home, _ = _find_home_and_resident(
        anchor_resident_phone
    )

    return start_daily_meal_poll(
        home,
        meal_date,
    )


def vote_on_daily_meal_poll(
    resident_phone: str,
    meal_date,
    selected_meal: str,
):
    """Submit a Resident's vote to their Home's poll."""

    home, resident = _find_home_and_resident(
        resident_phone
    )

    poll = d3database.find_poll(
        home,
        meal_date,
    )

    if poll is None:
        raise LookupError(
            "No daily meal poll exists for this Home "
            "and meal date."
        )

    return submit_meal_vote(
        poll,
        resident,
        selected_meal,
    )


def close_daily_meal_poll_for_home(
    anchor_resident_phone: str,
    meal_date,
):
    """Close the Home's poll and produce its final outcome."""

    home, _ = _find_home_and_resident(
        anchor_resident_phone
    )

    poll = d3database.find_poll(
        home,
        meal_date,
    )

    if poll is None:
        raise LookupError(
            "No daily meal poll exists for this Home "
            "and meal date."
        )

    return close_daily_meal_poll(
        poll
    )


def get_meal_summary(
    anchor_resident_phone: str,
    meal_date,
):
    """Retrieve the final MealSummary for a Home and date."""

    home, _ = _find_home_and_resident(
        anchor_resident_phone
    )

    summary = d3database.find_meal_summary(
        home,
        meal_date,
    )

    if summary is None:
        raise LookupError(
            "No MealSummary exists for this Home "
            "and meal date."
        )

    return summary