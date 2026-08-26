"""PostgreSQL repository for D3 daily meal coordination."""

from __future__ import annotations

from datetime import date

from database import get_connection

from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT import d1database
from DCD.Project_MEALBOT.D3_Daily_Meal_Coordination.d3business_obr import (
    DailyMealPoll,
    MealPlan,
    MealSummary,
    MealVote,
)


def _validate(home, meal_date: date) -> None:
    if home.id is None:
        raise ValueError(
            "A saved Home is required."
        )

    if not isinstance(meal_date, date):
        raise ValueError(
            "A valid meal date is required."
        )


def _hydrate_poll(connection, poll_row) -> DailyMealPoll:
    """
    Reconstruct a DailyMealPoll domain object from PostgreSQL.

    The repository owns persistence reconstruction; the domain object
    continues to own all voting and state-transition behaviour.
    """

    home = d1database.find_home_by_id(
        poll_row["home_id"]
    )

    if home is None:
        raise LookupError(
            "The Home belonging to this poll was not found."
        )

    poll = DailyMealPoll.__new__(
        DailyMealPoll
    )

    poll.id = poll_row["id"]
    poll.home = home
    poll.meal_date = poll_row["meal_date"]
    poll.status = poll_row["status"]
    poll.opened_at = poll_row["opened_at"]
    poll.closed_at = poll_row["closed_at"]

    poll._votes = []
    poll.option_ids = {}

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                id,
                meal_name
            FROM poll_options
            WHERE poll_id = %s
            ORDER BY rank
            """,
            (poll.id,),
        )

        option_rows = cursor.fetchall()

        poll.options = tuple(
            row["meal_name"]
            for row in option_rows
        )

        poll.option_ids = {
            row["meal_name"]: row["id"]
            for row in option_rows
        }

        cursor.execute(
            """
            SELECT
                id,
                poll_id,
                poll_option_id,
                resident_id,
                submitted_at
            FROM meal_votes
            WHERE poll_id = %s
            ORDER BY submitted_at
            """,
            (poll.id,),
        )

        vote_rows = cursor.fetchall()

        option_names_by_id = {
            row["id"]: row["meal_name"]
            for row in option_rows
        }

        for row in vote_rows:

            resident = d1database.find_resident_by_id(
                row["resident_id"]
            )

            if resident is None:
                raise LookupError(
                    "A MealVote references a Resident "
                    "that does not exist."
                )

            selected_meal = option_names_by_id.get(
                row["poll_option_id"]
            )

            if selected_meal is None:
                raise LookupError(
                    "A MealVote references a PollOption "
                    "that does not belong to this poll."
                )

            vote = MealVote(
                resident,
                selected_meal,
                row["submitted_at"],
            )

            vote.id = row["id"]

            poll._votes.append(
                vote
            )

    return poll


def find_poll(
    home,
    meal_date: date,
):
    """Find one Home's poll for a specific meal date."""

    _validate(
        home,
        meal_date,
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    home_id,
                    meal_date,
                    status,
                    opened_at,
                    closed_at
                FROM daily_meal_polls
                WHERE home_id = %s
                  AND meal_date = %s
                """,
                (
                    home.id,
                    meal_date,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return _hydrate_poll(
                connection,
                row,
            )


def save_poll(
    poll: DailyMealPoll,
) -> DailyMealPoll:
    """
    Persist a poll and any new votes.

    The entire poll update is committed atomically.
    """

    if poll.home.id is None:
        raise ValueError(
            "Home must be saved before saving a poll."
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:

            if poll.id is None:

                cursor.execute(
                    """
                    INSERT INTO daily_meal_polls (
                        home_id,
                        meal_date,
                        status,
                        opened_at,
                        closed_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        poll.home.id,
                        poll.meal_date,
                        poll.status,
                        poll.opened_at,
                        poll.closed_at,
                    ),
                )

                poll.id = cursor.fetchone()["id"]

                for rank, meal in enumerate(
                    poll.options,
                    start=1,
                ):
                    cursor.execute(
                        """
                        INSERT INTO poll_options (
                            poll_id,
                            meal_name,
                            rank
                        )
                        VALUES (%s, %s, %s)
                        RETURNING id
                        """,
                        (
                            poll.id,
                            meal,
                            rank,
                        ),
                    )

                    option_id = cursor.fetchone()["id"]

                    poll.option_ids[meal] = option_id

            else:

                cursor.execute(
                    """
                    UPDATE daily_meal_polls
                    SET
                        status = %s,
                        opened_at = %s,
                        closed_at = %s
                    WHERE id = %s
                    """,
                    (
                        poll.status,
                        poll.opened_at,
                        poll.closed_at,
                        poll.id,
                    ),
                )

            # Persist votes that do not yet have a database ID.
            for vote in poll.votes:

                if vote.id is not None:
                    continue

                option_id = poll.option_ids.get(
                    vote.selected_meal
                )

                if option_id is None:
                    raise ValueError(
                        "Vote references a meal that "
                        "is not a poll option."
                    )

                if vote.resident.id is None:
                    raise ValueError(
                        "Resident must be saved before voting."
                    )

                cursor.execute(
                    """
                    INSERT INTO meal_votes (
                        home_id,
                        poll_id,
                        poll_option_id,
                        resident_id,
                        submitted_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        poll.home.id,
                        poll.id,
                        option_id,
                        vote.resident.id,
                        vote.submitted_at,
                    ),
                )

                vote.id = cursor.fetchone()["id"]

    return poll


def list_polls(
    home=None,
) -> list[DailyMealPoll]:
    """Return persisted polls, optionally restricted to one Home."""

    with get_connection() as connection:
        with connection.cursor() as cursor:

            if home is None:

                cursor.execute(
                    """
                    SELECT
                        id,
                        home_id,
                        meal_date,
                        status,
                        opened_at,
                        closed_at
                    FROM daily_meal_polls
                    ORDER BY meal_date
                    """
                )

            else:

                if home.id is None:
                    raise ValueError(
                        "Home must be saved before listing its polls."
                    )

                cursor.execute(
                    """
                    SELECT
                        id,
                        home_id,
                        meal_date,
                        status,
                        opened_at,
                        closed_at
                    FROM daily_meal_polls
                    WHERE home_id = %s
                    ORDER BY meal_date
                    """,
                    (home.id,),
                )

            rows = cursor.fetchall()

            return [
                _hydrate_poll(
                    connection,
                    row,
                )
                for row in rows
            ]


def find_meal_summary(
    home,
    meal_date: date,
):
    """Find the persisted MealSummary for a Home/date."""

    _validate(
        home,
        meal_date,
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    ms.id,
                    ms.home_id,
                    ms.poll_id,
                    ms.winning_poll_option_id,
                    ms.total_votes,
                    ms.created_at
                FROM meal_summaries AS ms
                JOIN daily_meal_polls AS p
                    ON p.id = ms.poll_id
                WHERE ms.home_id = %s
                  AND p.meal_date = %s
                """,
                (
                    home.id,
                    meal_date,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            cursor.execute(
                """
                SELECT
                    id,
                    home_id,
                    meal_date,
                    status,
                    opened_at,
                    closed_at
                FROM daily_meal_polls
                WHERE id = %s
                """,
                (row["poll_id"],),
            )

            poll_row = cursor.fetchone()

            if poll_row is None:
                raise LookupError(
                    "MealSummary references a poll "
                    "that does not exist."
                )

            poll = _hydrate_poll(
                connection,
                poll_row,
            )

            winning_meal = next(
                (
                    meal
                    for meal, option_id
                    in poll.option_ids.items()
                    if option_id
                    == row["winning_poll_option_id"]
                ),
                None,
            )

            if winning_meal is None:
                raise LookupError(
                    "MealSummary references a poll option "
                    "that does not belong to its poll."
                )

            summary = MealSummary.__new__(
                MealSummary
            )

            summary.id = row["id"]
            summary.home = home
            summary.meal_date = poll.meal_date
            summary.winning_meal = winning_meal
            summary.vote_counts = poll.vote_counts()
            summary.total_votes = row["total_votes"]
            summary.poll = poll
            summary.created_at = row["created_at"]

            return summary


def save_meal_summary(
    summary: MealSummary,
) -> MealSummary:
    """Persist a closed poll's MealSummary."""

    if summary.home.id is None:
        raise ValueError(
            "Home must be saved before saving a MealSummary."
        )

    if summary.poll.id is None:
        raise ValueError(
            "Poll must be saved before saving a MealSummary."
        )

    winning_option_id = summary.poll.option_ids.get(
        summary.winning_meal
    )

    if winning_option_id is None:
        raise ValueError(
            "Winning meal is not a poll option."
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO meal_summaries (
                    home_id,
                    poll_id,
                    winning_poll_option_id,
                    total_votes,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    summary.home.id,
                    summary.poll.id,
                    winning_option_id,
                    summary.total_votes,
                    summary.created_at,
                ),
            )

            summary.id = cursor.fetchone()["id"]

    return summary


def list_meal_summaries(
    home=None,
) -> list[MealSummary]:
    """Return persisted MealSummaries."""

    with get_connection() as connection:
        with connection.cursor() as cursor:

            if home is None:

                cursor.execute(
                    """
                    SELECT
                        id,
                        home_id,
                        poll_id,
                        winning_poll_option_id,
                        total_votes,
                        created_at
                    FROM meal_summaries
                    ORDER BY created_at
                    """
                )

            else:

                if home.id is None:
                    raise ValueError(
                        "Home must be saved before listing summaries."
                    )

                cursor.execute(
                    """
                    SELECT
                        id,
                        home_id,
                        poll_id,
                        winning_poll_option_id,
                        total_votes,
                        created_at
                    FROM meal_summaries
                    WHERE home_id = %s
                    ORDER BY created_at
                    """,
                    (home.id,),
                )

            rows = cursor.fetchall()

            summaries = []

            for row in rows:

                poll = find_poll(
                    home
                    if home is not None
                    else d1database.find_home_by_id(
                        row["home_id"]
                    ),
                    None,
                )

                # This path is intentionally not used by the current
                # D3 runtime. find_meal_summary() is the canonical
                # Home/date lookup path.
                if poll is None:
                    continue

            # Rebuild through the canonical query below.
            summaries.clear()

            if home is not None:
                cursor.execute(
                    """
                    SELECT p.meal_date
                    FROM meal_summaries AS ms
                    JOIN daily_meal_polls AS p
                        ON p.id = ms.poll_id
                    WHERE ms.home_id = %s
                    ORDER BY p.meal_date
                    """,
                    (home.id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        ms.home_id,
                        p.meal_date
                    FROM meal_summaries AS ms
                    JOIN daily_meal_polls AS p
                        ON p.id = ms.poll_id
                    ORDER BY p.meal_date
                    """
                )

            lookup_rows = cursor.fetchall()

            for lookup_row in lookup_rows:

                target_home = (
                    home
                    if home is not None
                    else d1database.find_home_by_id(
                        lookup_row["home_id"]
                    )
                )

                if target_home is None:
                    continue

                summary = find_meal_summary(
                    target_home,
                    lookup_row["meal_date"],
                )

                if summary is not None:
                    summaries.append(summary)

            return summaries


def find_meal_plan(
    home,
    meal_date: date,
):
    """Find the persisted MealPlan for a Home/date."""

    _validate(
        home,
        meal_date,
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    mp.id,
                    mp.home_id,
                    mp.meal_summary_id,
                    mp.cook_id,
                    mp.meal_date,
                    mp.meal_name,
                    mp.vote_count,
                    mp.created_at
                FROM meal_plans AS mp
                WHERE mp.home_id = %s
                  AND mp.meal_date = %s
                """,
                (
                    home.id,
                    meal_date,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            cook = home.cook

            if cook is None:
                raise LookupError(
                    "MealPlan exists but the Home has no cook."
                )

            summary = find_meal_summary(
                home,
                meal_date,
            )

            if summary is None:
                raise LookupError(
                    "MealPlan references a MealSummary "
                    "that could not be reconstructed."
                )

            plan = MealPlan.__new__(
                MealPlan
            )

            plan.id = row["id"]
            plan.home = home
            plan.cook = cook
            plan.meal_date = row["meal_date"]
            plan.meal = row["meal_name"]
            plan.vote_count = row["vote_count"]
            plan.summary = summary

            return plan


def save_meal_plan(
    plan: MealPlan,
) -> MealPlan:
    """Persist the final MealPlan."""

    if plan.home.id is None:
        raise ValueError(
            "Home must be saved before saving a MealPlan."
        )

    if plan.summary.id is None:
        raise ValueError(
            "MealSummary must be saved before saving a MealPlan."
        )

    if plan.cook.id is None:
        raise ValueError(
            "Cook must be saved before saving a MealPlan."
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO meal_plans (
                    home_id,
                    meal_summary_id,
                    cook_id,
                    meal_date,
                    meal_name,
                    vote_count,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    plan.home.id,
                    plan.summary.id,
                    plan.cook.id,
                    plan.meal_date,
                    plan.meal,
                    plan.vote_count,
                    plan.summary.created_at,
                ),
            )

            plan.id = cursor.fetchone()["id"]

    return plan