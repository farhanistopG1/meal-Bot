"""D3 workflows that coordinate the daily meal decision lifecycle."""

from __future__ import annotations

from datetime import date, timedelta

from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT.d1business_obr import (
    Home,
    Resident,
)

from DCD.Project_MEALBOT.D2_MEAL_PLANNING import (
    d2database as meal_preference_database,
)

from DCD.Project_MEALBOT.D3_Daily_Meal_Coordination import (
    d3database,
)

from DCD.Project_MEALBOT.D3_Daily_Meal_Coordination.d3business_obr import (
    DailyMealPoll,
    HomeMenu,
    MealPlan,
    MealRecommendationEngine,
    MealSummary,
)


def _default_meal_date() -> date:
    """Return tomorrow as the default meal date."""
    return date.today() + timedelta(days=1)


def _preferences_for_home(home: Home):
    """
    Return the current MealPreference for each resident in the Home.

    D2 retains preference history. D3 only consumes the current preference
    for each resident participating in the Home's daily meal coordination.
    """
    resident_phones = {
        resident.phone
        for resident in home.residents
    }

    preferences_by_resident = {}

    for preference in meal_preference_database.list_meals():
        if preference.resident.phone in resident_phones:
            preferences_by_resident[
                preference.resident.phone
            ] = preference

    return list(preferences_by_resident.values())


def create_daily_meal_poll(
    home: Home,
    meal_date: date | None = None,
) -> DailyMealPoll:
    """
    Create and persist a Draft DailyMealPoll.

    The poll is not opened by this function.
    """
    home = HomeMenu._validate_active_home(home)

    target_date = meal_date or _default_meal_date()

    existing_poll = d3database.find_poll(
        home,
        target_date,
    )

    if existing_poll is not None:
        raise ValueError(
            "A poll already exists for this Home and meal date."
        )

    preferences = _preferences_for_home(home)

    if not preferences:
        raise ValueError(
            "No meal preferences exist for the residents of this Home."
        )

    home_menu = HomeMenu(
        home,
        preferences,
    )

    recommendation_engine = MealRecommendationEngine(
        home,
        home_menu,
        target_date,
    )

    poll = DailyMealPoll(
        home,
        recommendation_engine,
    )

    return d3database.save_poll(poll)


def open_daily_meal_poll(
    poll: DailyMealPoll,
) -> DailyMealPoll:
    """
    Open a previously created Draft poll for resident voting.
    """
    poll.open()

    return d3database.save_poll(poll)


def start_daily_meal_poll(
    home: Home,
    meal_date: date | None = None,
) -> DailyMealPoll:
    """
    Convenience workflow:
    create tomorrow's poll and immediately open it.
    """
    poll = create_daily_meal_poll(
        home,
        meal_date,
    )

    return open_daily_meal_poll(poll)


def submit_meal_vote(
    poll: DailyMealPoll,
    resident: Resident,
    selected_meal: str,
) -> DailyMealPoll:
    """
    Record one resident vote in an open poll and persist it.
    """
    poll.cast_vote(
        resident,
        selected_meal,
    )

    return d3database.save_poll(poll)


def close_daily_meal_poll(
    poll: DailyMealPoll,
) -> tuple[MealSummary, MealPlan]:
    """
    Close the poll and persist its final business outcome.

    The final outcome consists of:
        DailyMealPoll → MealSummary → MealPlan
    """
    existing_summary = d3database.find_meal_summary(
        poll.home,
        poll.meal_date,
    )

    if existing_summary is not None:
        raise ValueError(
            "A MealSummary already exists for this Home and meal date."
        )

    poll.close()

    d3database.save_poll(poll)

    summary = MealSummary(
        poll.home,
        poll,
    )

    summary = d3database.save_meal_summary(
        summary
    )

    plan = MealPlan(
        poll.home,
        summary,
    )

    plan = d3database.save_meal_plan(
        plan
    )

    return summary, plan