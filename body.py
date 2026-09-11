from __future__ import annotations

from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from organs import (
    add_resident_to_home as add_resident_to_home_workflow,
    close_daily_meal_poll_for_home,
    create_daily_meal_poll as create_daily_meal_poll_workflow,
    create_home as create_home_workflow,
    create_meal_preference as create_meal_preference_workflow,
    get_meal_summary as get_meal_summary_workflow,
    get_active_home_telegram_chat_id as get_active_home_telegram_chat_id_workflow,
    get_telegram_home_link as get_telegram_home_link_workflow,
    onboard_telegram_resident as onboard_telegram_resident_workflow,
    vote_on_daily_meal_poll,
)

from telegram_d3_readiness_reconciler import (
    run_reconciliation as run_d3_readiness_reconciliation,
)


app = FastAPI(
    title="MealBot API",
    version="1.0.0",
    description="API boundary for the MealBot daily meal coordination system.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class CreateHomeRequest(BaseModel):
    home_name: str
    resident_name: str
    resident_number: str
    cook_name: str
    cook_number: str
    telegram_chat_id: int


class AddResidentRequest(BaseModel):
    anchor_resident_phone: str
    resident_name: str
    resident_number: str


class TelegramResidentOnboardingRequest(BaseModel):
    chat_id: int
    telegram_user_id: int
    resident_name: str
    resident_number: str
    fav_meals: list[str]
    protein_preference: str
    spice_preference: str
    mode: str = "resident"


class SaveMealPreferenceRequest(BaseModel):
    resident_phone: str
    fav_meals: list[str]
    protein_preference: str
    spice_preference: str


class CreatePollRequest(BaseModel):
    anchor_resident_phone: str
    meal_date: date | None = None


class VoteRequest(BaseModel):
    resident_phone: str
    meal_date: date
    selected_meal: str


class ClosePollRequest(BaseModel):
    anchor_resident_phone: str
    meal_date: date


# ============================================================
# RESPONSE BUILDERS
# ============================================================

def _poll_response(poll):
    return {
        "poll_id": poll.id,
        "home_id": poll.home.id,
        "home_name": poll.home.name,
        "meal_date": poll.meal_date,
        "status": poll.status,
        "options": list(poll.options),
        "vote_counts": poll.vote_counts(),
    }


def _summary_response(summary):
    return {
        "summary_id": summary.id,
        "home_id": summary.home.id,
        "home_name": summary.home.name,
        "meal_date": summary.meal_date,
        "winning_meal": summary.winning_meal,
        "vote_counts": summary.vote_counts,
        "total_votes": summary.total_votes,
        "cook_name": (
            summary.home.cook.name
            if summary.home.cook
            else None
        ),
        "created_at": summary.created_at,
    }


def _meal_plan_response(meal_plan):
    return {
        "meal_plan_id": meal_plan.id,
        "home_id": meal_plan.home.id,
        "meal_date": meal_plan.meal_date,
        "meal": meal_plan.meal,
        "cook_name": meal_plan.cook.name,
        "vote_count": meal_plan.vote_count,
    }


# ============================================================
# D1 — HOME MANAGEMENT
# ============================================================

@app.post("/api/v1/homes")
def create_home(request: CreateHomeRequest):
    try:
        home = create_home_workflow(
            home_name=request.home_name,
            resident_name=request.resident_name,
            resident_number=request.resident_number,
            cook_name=request.cook_name,
            cook_number=request.cook_number,
            telegram_chat_id=request.telegram_chat_id,
        )

        return {
            "home_id": home.id,
            "home_name": home.name,
            "status": home.status,
            "resident_count": len(home.residents),
            "cook_name": (
                home.cook.name
                if home.cook
                else None
            ),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@app.post("/api/v1/residents/telegram-onboarding")
def onboard_telegram_resident(
    request: TelegramResidentOnboardingRequest,
):
    try:
        resident, meal_preference = (
            onboard_telegram_resident_workflow(
                chat_id=request.chat_id,
                telegram_user_id=request.telegram_user_id,
                resident_name=request.resident_name,
                resident_number=request.resident_number,
                fav_meals=request.fav_meals,
                protein_preference=request.protein_preference,
                spice_preference=request.spice_preference,
                mode=request.mode,
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
        "resident_id": resident.id,
        "resident_name": resident.name,
        "resident_phone": resident.phone,
        "resident_status": resident.status,
        "preference_id": meal_preference.id,
        "fav_meals": sorted(
            meal_preference.fav_meals
        ),
        "protein_preference": (
            meal_preference.protein_preference
        ),
        "spice_preference": (
            meal_preference.spice_preference
        ),
        "version": meal_preference.version,
    }


@app.post("/api/v1/homes/residents")
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
        "resident_id": resident.id,
        "resident_name": resident.name,
        "resident_phone": resident.phone,
        "status": resident.status,
    }


# ============================================================
# TRANSPORT — HOME → TELEGRAM RESOLUTION
# ============================================================

@app.get("/api/v1/transport/telegram/home/{home_id}")
def get_active_home_telegram_chat_id(
    home_id: str,
):
    try:
        chat_id = get_active_home_telegram_chat_id_workflow(
            home_id=home_id,
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    if chat_id is None:
        raise HTTPException(
            status_code=404,
            detail="No active Telegram group is linked to this Home.",
        )

    return {
        "home_id": home_id,
        "chat_id": chat_id,
    }


# ============================================================
# TRANSPORT — TELEGRAM → HOME RESOLUTION
# ============================================================

@app.get("/api/v1/transport/telegram/{chat_id}")
def get_telegram_home_link(
    chat_id: int,
):
    try:
        link = get_telegram_home_link_workflow(
            chat_id=chat_id,
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    return {
        "chat_id": chat_id,
        "linked": link is not None,
        "home_id": (
            link["home_id"]
            if link is not None
            else None
        ),
    }

# ============================================================
# D2 — MEAL PREFERENCES
# ============================================================

@app.post("/api/v1/residents/meal-preferences")
def save_meal_preference(
    request: SaveMealPreferenceRequest,
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
        "preference_id": meal_preference.id,
        "resident_id": meal_preference.resident.id,
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
        "version": meal_preference.version,
    }


# ============================================================
# D3 — DAILY MEAL COORDINATION
# ============================================================

@app.post("/api/v1/homes/meal-polls")
def create_daily_meal_poll(
    request: CreatePollRequest,
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


@app.post("/api/v1/meal-polls/votes")
def cast_daily_meal_vote(
    request: VoteRequest,
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


@app.post("/api/v1/meal-polls/close")
def close_daily_meal_poll(
    request: ClosePollRequest,
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
        "summary": _summary_response(summary),
        "meal_plan": _meal_plan_response(meal_plan),
    }


# ============================================================
# D3 — RESULTS
# ============================================================

@app.get(
    "/api/v1/homes/meal-summaries/{anchor_resident_phone}/{meal_date}"
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

# ============================================================
# N3 — D3 READINESS RECONCILIATION
# ============================================================

@app.get("/api/v1/d3/readiness")
async def read_d3_readiness():
    try:
        results = await run_d3_readiness_reconciliation()

        return {
            "results": results,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="D3 readiness reconciliation failed.",
        ) from error
