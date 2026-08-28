"""Shared PostgreSQL infrastructure. Domain repositories own all SQL."""

from __future__ import annotations

import psycopg
from psycopg.rows import dict_row


def get_connection() -> psycopg.Connection:
    """Open a connection to the MealBot PostgreSQL database."""
    return psycopg.connect(
        dbname="mealbot",
        user="mealbot",
        password="your_password",
        host="localhost",
        row_factory=dict_row,
    )
