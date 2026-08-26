"""D3 domain objects, behaviours, and rules for daily meal coordination.

This module contains business logic only.

Persistence is owned by d3database.py.
Workflow orchestration is owned by d3business_workflow.py.
External transport and scheduling are outside the D3 domain.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone

from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT.d1business_obr import (
    Home,
    Resident,
)
from DCD.Project_MEALBOT.D2_MEAL_PLANNING.d2business_obr import (
    MealPreference,
)


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class HomeMenu:
    """The meals an active Home can consider, ranked by resident popularity."""

    def __init__(
        self,
        home: Home,
        meal_preferences: list[MealPreference],
    ) -> None:
        self.home = self._validate_active_home(home)
        self._meal_counts = self._build_meal_counts(
            meal_preferences
        )

    @staticmethod
    def _validate_active_home(home: Home) -> Home:
        if not isinstance(home, Home):
            raise ValueError("A valid Home is required.")

        if home.status != "Active":
            raise ValueError("The Home must be Active.")

        return home

    def _build_meal_counts(
        self,
        preferences: list[MealPreference],
    ) -> Counter[str]:

        if not preferences:
            raise ValueError(
                "At least one MealPreference is required."
            )

        home_residents = {
            resident.phone
            for resident in self.home.residents
        }

        counts: Counter[str] = Counter()
        preference_owners: set[str] = set()

        for preference in preferences:

            if not isinstance(
                preference,
                MealPreference,
            ):
                raise ValueError(
                    "Every item must be a valid MealPreference."
                )

            if preference.resident.phone not in home_residents:
                raise ValueError(
                    "A MealPreference must belong to a resident "
                    "of this Home."
                )

            if preference.resident.phone in preference_owners:
                raise ValueError(
                    "A HomeMenu can contain only one "
                    "MealPreference per resident."
                )

            preference_owners.add(
                preference.resident.phone
            )

            if preference.resident.status != "Active":
                continue

            counts.update(
                preference.fav_meals
            )

        if not counts:
            raise ValueError(
                "The Home has no active resident "
                "meal preferences."
            )

        return counts

    @property
    def available_meals(self) -> set[str]:
        return set(self._meal_counts)

    def expose_home_meals(self) -> set[str]:
        return self.available_meals

    def is_meal_available(
        self,
        meal: str,
    ) -> bool:

        return (
            isinstance(meal, str)
            and meal.strip().lower() in self._meal_counts
        )

    def popularity_of(
        self,
        meal: str,
    ) -> int:

        if not isinstance(meal, str):
            raise ValueError(
                "Meal must be a string."
            )

        return self._meal_counts[
            meal.strip().lower()
        ]

    def rank_meals(self) -> list[str]:
        """
        Return meals from most popular to least popular.

        Alphabetical order resolves equal-popularity ties
        deterministically.
        """
        return sorted(
            self._meal_counts,
            key=lambda meal: (
                -self._meal_counts[meal],
                meal,
            ),
        )


class MealRecommendationEngine:
    """Chooses the three poll candidates from a Home's valid menu."""

    def __init__(
        self,
        home: Home,
        home_menu: HomeMenu,
        meal_date: date | None = None,
    ) -> None:

        self.home = HomeMenu._validate_active_home(
            home
        )

        if not isinstance(
            home_menu,
            HomeMenu,
        ):
            raise ValueError(
                "A valid HomeMenu is required."
            )

        if home_menu.home is not home:
            raise ValueError(
                "The HomeMenu must belong to "
                "the supplied Home."
            )

        if len(home_menu.available_meals) < 3:
            raise ValueError(
                "At least three distinct meals are "
                "required to create a poll."
            )

        self.home_menu = home_menu

        self.recommendation_date = (
            self._validate_future_date(
                meal_date
                or date.today() + timedelta(days=1)
            )
        )

        self.recommended_meals = (
            home_menu.rank_meals()[:3]
        )

    @staticmethod
    def _validate_future_date(
        meal_date: date,
    ) -> date:

        if not isinstance(
            meal_date,
            date,
        ):
            raise ValueError(
                "Meal date must be a date."
            )

        if meal_date <= date.today():
            raise ValueError(
                "Recommendations must be "
                "for a future date."
            )

        return meal_date

    def expose_recommendations(
        self,
    ) -> list[str]:

        return list(
            self.recommended_meals
        )


class MealVote:
    """
    An immutable business fact that one resident
    selected one option in one poll.
    """

    def __init__(
        self,
        resident: Resident,
        selected_meal: str,
        submitted_at: datetime | None = None,
    ) -> None:

        if not isinstance(
            resident,
            Resident,
        ):
            raise ValueError(
                "A valid Resident is required."
            )

        if resident.status != "Active":
            raise ValueError(
                "Only active residents may vote."
            )

        if (
            not isinstance(
                selected_meal,
                str,
            )
            or not selected_meal.strip()
        ):
            raise ValueError(
                "A selected meal is required."
            )

        self.id = None

        self.resident = resident

        self.selected_meal = (
            selected_meal.strip().lower()
        )

        self.submitted_at = (
            submitted_at
            or _utc_now()
        )


class DailyMealPoll:
    """One Home's voting process for one future meal date."""

    DRAFT = "Draft"
    OPEN = "Open"
    CLOSED = "Closed"

    def __init__(
        self,
        home: Home,
        recommendation_engine: MealRecommendationEngine,
    ) -> None:

        self.id = None

        self.home = (
            HomeMenu._validate_active_home(home)
        )

        self.option_ids: dict[str, object] = {}

        if not isinstance(
            recommendation_engine,
            MealRecommendationEngine,
        ):
            raise ValueError(
                "A valid MealRecommendationEngine "
                "is required."
            )

        if recommendation_engine.home is not home:
            raise ValueError(
                "The recommendation engine must "
                "belong to this Home."
            )

        self.meal_date = (
            recommendation_engine.recommendation_date
        )

        self.options = tuple(
            recommendation_engine.expose_recommendations()
        )

        self.status = self.DRAFT

        self.opened_at: datetime | None = None
        self.closed_at: datetime | None = None

        self._votes: list[MealVote] = []

    @property
    def votes(
        self,
    ) -> tuple[MealVote, ...]:

        return tuple(
            self._votes
        )

    def open(self) -> None:

        if self.status != self.DRAFT:
            raise ValueError(
                "Only a draft poll can be opened."
            )

        self.status = self.OPEN
        self.opened_at = _utc_now()

    def cast_vote(
        self,
        resident: Resident,
        selected_meal: str,
    ) -> MealVote:

        if self.status != self.OPEN:
            raise ValueError(
                "Votes can only be submitted "
                "while the poll is open."
            )

        if not isinstance(
            resident,
            Resident,
        ):
            raise ValueError(
                "A valid Resident is required."
            )

        if resident.phone not in {
            member.phone
            for member in self.home.residents
        }:
            raise ValueError(
                "Only residents of this Home "
                "may vote."
            )

        if resident.status != "Active":
            raise ValueError(
                "Only active residents may vote."
            )

        if any(
            vote.resident.phone
            == resident.phone
            for vote in self._votes
        ):
            raise ValueError(
                "A resident may vote only once per poll."
            )

        vote = MealVote(
            resident,
            selected_meal,
        )

        if vote.selected_meal not in self.options:
            raise ValueError(
                "The selected meal is not a poll option."
            )

        self._votes.append(vote)

        return vote

    def vote_counts(
        self,
    ) -> dict[str, int]:

        counts = Counter(
            vote.selected_meal
            for vote in self._votes
        )

        return {
            meal: counts[meal]
            for meal in self.options
        }

    def close(self) -> None:

        if self.status != self.OPEN:
            raise ValueError(
                "Only an open poll can be closed."
            )

        if not self._votes:
            raise ValueError(
                "A poll needs at least one vote "
                "before it can close."
            )

        self.status = self.CLOSED
        self.closed_at = _utc_now()

    def winning_meal(self) -> str:

        if self.status != self.CLOSED:
            raise ValueError(
                "The winning meal is available "
                "only after the poll closes."
            )

        counts = self.vote_counts()

        return sorted(
            self.options,
            key=lambda meal: (
                -counts[meal],
                meal,
            ),
        )[0]


class MealSummary:
    """The recorded outcome of one closed DailyMealPoll."""

    def __init__(
        self,
        home: Home,
        daily_meal_poll: DailyMealPoll,
    ) -> None:

        self.id = None

        self.home = (
            HomeMenu._validate_active_home(home)
        )

        if not isinstance(
            daily_meal_poll,
            DailyMealPoll,
        ):
            raise ValueError(
                "A valid DailyMealPoll is required."
            )

        if daily_meal_poll.home is not home:
            raise ValueError(
                "The poll must belong to this Home."
            )

        if (
            daily_meal_poll.status
            != DailyMealPoll.CLOSED
        ):
            raise ValueError(
                "A MealSummary can only be created "
                "from a closed poll."
            )

        self.meal_date = (
            daily_meal_poll.meal_date
        )

        self.winning_meal = (
            daily_meal_poll.winning_meal()
        )

        self.vote_counts = (
            daily_meal_poll.vote_counts()
        )

        self.total_votes = len(
            daily_meal_poll.votes
        )

        self.poll = daily_meal_poll

        self.created_at = _utc_now()


class MealPlan:
    """
    The final operational instruction:

    this Home will prepare this meal
    on this date for its current cook.
    """

    def __init__(
        self,
        home: Home,
        meal_summary: MealSummary,
    ) -> None:

        self.id = None

        self.home = (
            HomeMenu._validate_active_home(home)
        )

        if not isinstance(
            meal_summary,
            MealSummary,
        ):
            raise ValueError(
                "A valid MealSummary is required."
            )

        if meal_summary.home is not home:
            raise ValueError(
                "The MealSummary must belong "
                "to this Home."
            )

        if home.cook is None:
            raise ValueError(
                "A Home must have a cook before "
                "a MealPlan can be created."
            )

        self.cook = home.cook

        self.meal_date = (
            meal_summary.meal_date
        )

        self.meal = (
            meal_summary.winning_meal
        )

        self.vote_count = (
            meal_summary.vote_counts[
                self.meal
            ]
        )

        self.summary = meal_summary

        # Required by the PostgreSQL persistence layer.
        # This is the moment the immutable MealPlan
        # business object is created.
        self.created_at = _utc_now()