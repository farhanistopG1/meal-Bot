from __future__ import annotations
from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT.d1business_obr import Home, Resident, Cook
from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT import d1database


def configure_home(
        home_name:str, 
        resident_name:str,
        resident_number:str,
        cook_name: str,
        cook_number:str,
        ) -> Home:
    
    home = Home(home_name)
    resident = Resident(resident_name, resident_number)
    home.add_resident(resident)
    cook = Cook(cook_name, cook_number)
    home.assign_cook(cook)
    d1database.save(home)

    return home


#============== Test 
'''
home = configure_home(
    home_name = "Mudgal Home",
    resident_name= "Farhan",
    resident_number="+919606171365",
    cook_name="Sita",
    cook_number="+918123912521"
)

print(d1database.list_homes())
'''
#=============
