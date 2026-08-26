from __future__ import annotations

from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


from organs import (
    add_resident_to_home as add_resident_to_home_workflow,
    close_daily_meal_poll_for_home,
    create_daily_meal_poll as create_daily_meal_poll_workflow,
    create_home as create_home_workflow,
    create_meal_preference as create_meal_preference_workflow,
    get_meal_summary as get_meal_summary_workflow,
    vote_on_daily_meal_poll,
)


app = FastAPI()


class HomeRequest(BaseModel):
    home_name: str
    resident_name: str
    resident_number: str
    cook_name: str
    cook_number: str


class MealRequest(BaseModel):
    resident_phone: str
    fav_meals: list[str]
    protein_preference: str
    spice_preference: str


class AddResidentRequest(BaseModel):
    anchor_resident_phone: str
    resident_name: str
    resident_number: str


class DailyMealPollRequest(BaseModel):
    anchor_resident_phone: str
    meal_date: date | None = None


class MealVoteRequest(BaseModel):
    resident_phone: str
    meal_date: date
    selected_meal: str


class CloseDailyMealPollRequest(BaseModel):
    anchor_resident_phone: str
    meal_date: date


def _poll_response(poll):
    return {
        "home_name": poll.home.name,
        "meal_date": poll.meal_date,
        "status": poll.status,
        "options": list(poll.options),
        "vote_counts": poll.vote_counts(),
    }


def _summary_response(summary):
    return {
        "home_name": summary.home.name,
        "meal_date": summary.meal_date,
        "winning_meal": summary.winning_meal,
        "vote_counts": summary.vote_counts,
        "total_votes": summary.total_votes,
        "cook_name": summary.home.cook.name,
        "created_at": summary.created_at,
    }


@app.post("/homes")
def create_home(request: HomeRequest):
    try:
        home = create_home_workflow(
            home_name=request.home_name,
            resident_name=request.resident_name,
            resident_number=request.resident_number,
            cook_name=request.cook_name,
            cook_number=request.cook_number,
        )

        return {
            "home_name": home.name,
            "home_id": home.id,
            "status": home.status,
            "resident_count": len(home.residents),
            "cook_name": home.cook.name if home.cook else None,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@app.post("/homes/residents")
def add_resident_to_home(
    request: AddResidentRequest,
):
    try:
        resident = add_resident_to_home_workflow(
            anchor_resident_phone=request.anchor_resident_phone,
            resident_name=request.resident_name,
            resident_number=request.resident_number,
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return {
        "resident_name": resident.name,
        "resident_phone": resident.phone,
        "status": resident.status,
    }


@app.post("/meal_preference")
def create_meal_preference(
    request: MealRequest,
):
    try:
        meal_preference = create_meal_preference_workflow(
            resident_phone=request.resident_phone,
            fav_meals=request.fav_meals,
            protein_preference=request.protein_preference,
            spice_preference=request.spice_preference,
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return {
        "resident_name": meal_preference.resident.name,
        "resident_phone": meal_preference.resident.phone,
        "fav_meals": sorted(
            meal_preference.fav_meals
        ),
        "protein_preference": (
            meal_preference.protein_preference
        ),
        "spice_preference": (
            meal_preference.spice_preference
        ),
        "preference_id": meal_preference.id,
        "version": meal_preference.version,
    }


@app.post("/daily-meal-polls")
def create_daily_meal_poll(
    request: DailyMealPollRequest,
):
    try:
        poll = create_daily_meal_poll_workflow(
            anchor_resident_phone=(
                request.anchor_resident_phone
            ),
            meal_date=request.meal_date,
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return _poll_response(poll)


@app.post("/daily-meal-polls/votes")
def cast_daily_meal_vote(
    request: MealVoteRequest,
):
    try:
        poll = vote_on_daily_meal_poll(
            resident_phone=request.resident_phone,
            meal_date=request.meal_date,
            selected_meal=request.selected_meal,
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return _poll_response(poll)


@app.post("/daily-meal-polls/close")
def close_daily_meal_poll(
    request: CloseDailyMealPollRequest,
):
    try:
        summary, meal_plan = (
            close_daily_meal_poll_for_home(
                anchor_resident_phone=(
                    request.anchor_resident_phone
                ),
                meal_date=request.meal_date,
            )
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return {
        **_summary_response(summary),
        "meal_plan": {
            "meal": meal_plan.meal,
            "meal_date": meal_plan.meal_date,
            "cook_name": meal_plan.cook.name,
            "vote_count": meal_plan.vote_count,
        },
    }


@app.get(
    "/meal-summaries/{anchor_resident_phone}/{meal_date}"
)
def read_meal_summary(
    anchor_resident_phone: str,
    meal_date: date,
):
    try:
        summary = get_meal_summary_workflow(
            anchor_resident_phone,
            meal_date,
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return _summary_response(summary)