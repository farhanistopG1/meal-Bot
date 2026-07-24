from __future__ import annotations

from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT.body import Resident


class MealPreference:
    ALLOWED_PROTEIN_PREFERENCES = {
        "vegetarian",
        "egg",
        "non_vegetarian",
    }

    ALLOWED_SPICE_PREFERENCES = {
        "mild",
        "medium",
        "spicy",
    }

    def __init__(
        self,
        resident: Resident,
        fav_meals: list[str],
        protein_preference: str,
        spice_preference: str,
    ) -> None:

        if not isinstance(resident, Resident):
            raise ValueError("A valid Resident is required.")

        self.resident = resident
        self.fav_meals = self._validate_fav_meals(fav_meals)

        self.protein_preference = self._validate_preference(
            protein_preference,
            self.ALLOWED_PROTEIN_PREFERENCES,
        )

        self.spice_preference = self._validate_preference(
            spice_preference,
            self.ALLOWED_SPICE_PREFERENCES,
        )

    def update_protein_preference(
        self,
        protein_preference: str,
    ) -> None:

        self.protein_preference = self._validate_preference(
            protein_preference,
            self.ALLOWED_PROTEIN_PREFERENCES,
        )

    def update_spice_preference(
        self,
        spice_preference: str,
    ) -> None:

        self.spice_preference = self._validate_preference(
            spice_preference,
            self.ALLOWED_SPICE_PREFERENCES,
        )

    def update_fav_meals(
        self,
        fav_meals: list[str],
    ) -> None:

        self.fav_meals = self._validate_fav_meals(fav_meals)

    @staticmethod
    def _validate_fav_meals(
        fav_meals: list[str],
    ) -> set[str]:

        # Basket Validation
        if len(fav_meals) != 5:
            raise ValueError(
                "A resident must choose exactly 5 favourite meals."
            )

        cleaned_basket = set()

        # Item Validation + Normalization
        for meal in fav_meals:

            if not isinstance(meal, str):
                raise ValueError(
                    "Every favourite meal must be a string."
                )

            cleaned_meal = meal.strip().lower()

            if not cleaned_meal:
                raise ValueError(
                    "Favourite meal names cannot be empty."
                )

            cleaned_basket.add(cleaned_meal)

        # Collection Validation
        if len(cleaned_basket) != 5:
            raise ValueError(
                "Duplicate meals detected. A resident must choose 5 unique favourite meals."
            )

        return cleaned_basket

    @staticmethod
    def _validate_preference(
        preference: str,
        allowed_preferences: set[str],
    ) -> str:

        if not isinstance(preference, str):
            raise ValueError(
                "Preference must be a string."
            )

        normalized_preference = preference.strip().lower()

        if normalized_preference not in allowed_preferences:
            raise ValueError(
                f"Preference must be one of: {', '.join(sorted(allowed_preferences))}."
            )

        return normalized_preference

    def __repr__(self) -> str:
        return str(self.__dict__)