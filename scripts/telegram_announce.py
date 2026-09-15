import json
import sys
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from telegram_config import BOT_TOKEN


def send_message(chat_id, message):
    url = (
        "https://api.telegram.org/bot"
        + BOT_TOKEN
        + "/sendMessage"
    )

    payload = {
        "chat_id": str(chat_id),
        "text": message,
    }

    data = json.dumps(payload).encode()

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request) as response:
        response_data = json.loads(
            response.read().decode()
        )

    if not response_data.get("ok"):
        raise RuntimeError(
            f"Telegram sendMessage failed: {response_data}"
        )

    return response_data


def build_announcement(result):
    summary = result["summary"]
    meal_plan = result["meal_plan"]

    return (
        "🍽️ MealBot — Meal Decided\n\n"
        f"The group has decided: {summary['winning_meal']}\n\n"
        f"📅 Date: {summary['meal_date']}\n"
        f"🗳️ Votes: {summary['total_votes']}\n"
        f"👩‍🍳 Cook: {meal_plan['cook_name']}"
    )


if __name__ == "__main__":
    input_data = sys.stdin.read().strip()

    if not input_data:
        raise ValueError("No JSON supplied.")

    payload = json.loads(input_data)

    chat_id = payload["chat_id"]
    result = payload["result"]

    message = build_announcement(result)

    send_message(
        chat_id,
        message,
    )

    print("Telegram announcement sent.")
