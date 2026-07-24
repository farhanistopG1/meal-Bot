from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import DCD.Project_MEALBOT.D1_HOME_MANAGEMENT.database as home_database
import DCD.Project_MEALBOT.D2_MEAL_PLANNING.database as meal_preference_database
from organs import (
    create_home as create_home_workflow,
    create_meal_preference as create_meal_preference_workflow,
)

app = FastAPI()

class HomeRequest(BaseModel):
    home_name: str
    resident_name: str
    resident_number: str
    cook_name : str
    cook_number : str

class MealRequest(BaseModel):
    resident_phone: str
    fav_meals: list[str]
    protein_preference: str
    spice_preference: str


@app.post("/homes")
def create_home(request: HomeRequest):
    create_home_workflow(
        home_name=request.home_name,
        resident_name=request.resident_name,
        resident_number=request.resident_number,
        cook_name=request.cook_name,
        cook_number=request.cook_number,
    )

    return home_database.list_homes()

@app.post("/meal_preference")
def create_meal_preference(request: MealRequest):
    try:
        meal_preference = create_meal_preference_workflow(
            resident_phone=request.resident_phone,
            fav_meals=request.fav_meals,
            protein_preference=request.protein_preference,
            spice_preference=request.spice_preference,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return {
        "resident_name": meal_preference.resident.name,
        "resident_phone": meal_preference.resident.phone,
        "fav_meals": sorted(meal_preference.fav_meals),
        "protein_preference": meal_preference.protein_preference,
        "spice_preference": meal_preference.spice_preference,
        "saved_preferences": len(meal_preference_database.list_meals()),
    }






    
