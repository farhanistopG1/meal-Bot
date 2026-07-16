from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class MESSAGE(BaseModel):
    message = str 
    text = str 
    