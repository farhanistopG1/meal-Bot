from __future__ import annotations

from datetime import datetime, timezone


# ---------------------------- Business Objects, Behaviours and Rules.


class Home:
    def __init__(self, name: str):

        if not name.strip():
            raise ValueError("Home must have a name.")

        self.id = None
        self.name = name.strip()
        self.status = "Active"
        self.created_at = datetime.now(timezone.utc)
        self.residents = []
        self.cook = None

    def activate(self) -> None:
        if self.status == "Active":
            return

        self.status = "Active"

    def archive(self) -> None:
        if self.status == "Archived":
            return

        self.status = "Archived"

    def add_resident(self, resident: Resident) -> None:
        if resident in self.residents:
            return

        self.residents.append(resident)

    def assign_cook(self, cook: Cook) -> None:
        if self.cook == cook:
            return

        self.cook = cook

    def remove_resident(self, resident: Resident) -> None:
        if resident not in self.residents:
            return

        self.residents.remove(resident)

    def __repr__(self):
        return (
            f"Home(\n"
            f"    name='{self.name}',\n"
            f"    status='{self.status}',\n"
            f"    residents={self.residents},\n"
            f"    cook={self.cook}\n"
            f")"
        )


class Resident:
    def __init__(
        self,
        name: str,
        phone: str,
    ) -> None:

        if not name.strip():
            raise ValueError(
                "Resident name cannot be empty"
            )

        if not phone.strip():
            raise ValueError(
                "Resident Phone Number cannot be empty and must be Valid"
            )

        self.id = None
        self.name = name.strip()
        self.phone = phone.strip()
        self.status = "Active"
        self.onboarded_at = datetime.now(timezone.utc)

    def __repr__(self):
        return (
            f"Resident("
            f"name='{self.name}', "
            f"phone='{self.phone}', "
            f"status='{self.status}')"
        )


class Cook:
    def __init__(
        self,
        name: str,
        phone: str,
    ) -> None:

        if not name.strip():
            raise ValueError(
                "Cook name cannot be empty"
            )

        if not phone.strip():
            raise ValueError(
                "Cook Phone number cannot be Empty and must be valid"
            )

        self.id = None
        self.name = name.strip()
        self.phone = phone.strip()
        self.status = "Active"
        self.assigned_at = datetime.now(timezone.utc)

    def __repr__(self):
        return (
            f"Cook("
            f"name='{self.name}', "
            f"phone='{self.phone}', "
            f"status='{self.status}')"
        )