from fastapi import FastAPI
from pydantic import BaseModel
from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT.organs import configure_home
import DCD.Project_MEALBOT.D1_HOME_MANAGEMENT.database as database

app = FastAPI()

class Home_Request(BaseModel):
    home_name: str
    resident_name: str
    resident_number: str
    cook_name : str
    cook_number : str

@app.post("/homes")
def create_home(request: Home_Request):
    configure_home(
    home_name=request.home_name,
    resident_name=request.resident_name,
    resident_number=request.resident_number,
    cook_name=request.cook_name,
    cook_number=request.cook_number,
    )
    
    return database.list_homes()
    
