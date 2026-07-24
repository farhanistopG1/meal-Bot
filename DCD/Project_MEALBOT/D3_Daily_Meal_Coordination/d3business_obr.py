from __future__ import annotations
from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT.body import Home
from DCD.Project_MEALBOT.D2_MEAL_PLANNING.d2business_obr import MealPreference


# Object HomeMenu has two behaviours:
# 1. Expose its available meals.
# 2. Confirm whether the proposed meal exists inside it.
class HomeMenu:
    def __init__(
            self,
            home: Home,
            meal_preferences: list[MealPreference],
            protein_preference: list[MealPreference],
            spice_preference: list[MealPreference]
    ):

        self.home = self._validate_home(home)
        self.available_meals = self._build_available_meals(meal_preferences)
        self.protein_preferences = self._build_protein_preference(protein_preference)
        self.spice_preferences = self._build_spice_preference(spice_preference)

    @staticmethod
    def _validate_home(home: Home):
        if not isinstance(home, Home):
            raise ValueError("A valid Home must exist to proceed")

        if home.status != "Active":
            raise LookupError("The Home is not Active")

        return home

    @staticmethod
    def _build_available_meals(
        meal_preferences: list[MealPreference]
    ):
        available_meals = set()
        for preference in meal_preferences:
            if not isinstance(preference, MealPreference):
                raise ValueError("Every preference of the resident must comply MealPreference rules")

            available_meals.update(preference.fav_meals)
        return available_meals

    @staticmethod
    def _build_protein_preference(
        protein_preferences: list[MealPreference]
    ):
        preferences = []
        for preference in protein_preferences:
            if not isinstance(preference, MealPreference):
                raise ValueError("Every Preference of the resident must comply MealPreference rules")

            preferences.append(preference.protein_preference)

        return preferences

    @staticmethod
    def _build_spice_preference(
        spice_preferences: list[MealPreference]
    ):
        preferences = []
        for preference in spice_preferences:
            if not isinstance(preference, MealPreference):
                raise ValueError("Every Preference of the resident must comply MealPreference rules")

            preferences.append(preference.spice_preference)

        return preferences
    
    def expose_home_meals(self):
        return self.available_meals
    
    def is_meal_available(self, meal: str):
        return meal.strip().lower() in self.available_meals
    


    

    
