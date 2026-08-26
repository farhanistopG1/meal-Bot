"""Shared PostgreSQL infrastructure. Domain repositories own all SQL."""

from __future__ import annotations

import os

import psycopg
from psycopg.rows import dict_row


def get_connection() -> psycopg.Connection:
    """Open a local MealBot database connection without embedding credentials."""
    connection_args = {"dbname": os.getenv("MEALBOT_DB_NAME", "mealbot"), "row_factory": dict_row}
    database_user = os.getenv("MEALBOT_DB_USER")
    if database_user:
        connection_args["user"] = database_user
    return psycopg.connect(**connection_args)
