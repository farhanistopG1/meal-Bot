import asyncio
from datetime import date, timedelta

from telethon import TelegramClient

from telegram_config import API_ID, API_HASH, BOT_TOKEN
import transport_database
from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT import d1database as home_database
from DCD.Project_MEALBOT.D2_MEAL_PLANNING import d2database as preference_database
from DCD.Project_MEALBOT.D3_Daily_Meal_Coordination import d3database as meal_database


SESSION_NAME = "mealbot_d3_readiness"
MIN_CONFIGURED_RESIDENTS = 2


client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH,
)


def tomorrow():
    return date.today() + timedelta(days=1)


def get_active_telegram_homes():
    home_ids = set()

    for chat_id in transport_database.find_active_telegram_chats():
        link = transport_database.find_telegram_home_link(int(chat_id))

        if link is not None:
            home_ids.add(link["home_id"])

    return home_ids


def get_configured_resident_ids(home):
    preferences = preference_database.list_meals()

    active_resident_ids = {
        resident.id
        for resident in home.residents
        if resident.status == "Active"
    }

    return {
        preference.resident.id
        for preference in preferences
        if preference.resident.id in active_resident_ids
    }


def inspect_home(home_id, meal_date):
    home = home_database.find_home_by_id(home_id)

    if home is None:
        return {
            "home_id": home_id,
            "ready": False,
            "action": "WAIT",
            "reasons": ["HOME_NOT_FOUND"],
        }

    active_residents = [
        resident
        for resident in home.residents
        if resident.status == "Active"
    ]

    configured_ids = get_configured_resident_ids(home)

    configured_residents = [
        resident
        for resident in active_residents
        if resident.id in configured_ids
    ]

    existing_poll = meal_database.find_poll(home, meal_date)

    home_active = home.status == "Active"
    enough_residents = len(active_residents) >= MIN_CONFIGURED_RESIDENTS
    enough_preferences = (
        len(configured_residents) >= MIN_CONFIGURED_RESIDENTS
    )
    poll_exists = existing_poll is not None

    ready = (
        home_active
        and enough_residents
        and enough_preferences
        and not poll_exists
    )

    reasons = []

    if not home_active:
        reasons.append("HOME_NOT_ACTIVE")

    if not enough_residents:
        reasons.append(
            f"ACTIVE_RESIDENTS_BELOW_{MIN_CONFIGURED_RESIDENTS}"
        )

    if not enough_preferences:
        reasons.append(
            f"CONFIGURED_PREFERENCES_BELOW_{MIN_CONFIGURED_RESIDENTS}"
        )

    if poll_exists:
        reasons.append("TOMORROW_POLL_ALREADY_EXISTS")

    return {
        "home_id": home.id,
        "home_name": home.name,
        "home_status": home.status,
        "anchor_resident_phone": home.residents[0].phone,
        "active_residents": len(active_residents),
        "configured_residents": len(configured_residents),
        "tomorrow": meal_date,
        "poll_exists": poll_exists,
        "poll_id": str(existing_poll.id) if existing_poll else None,
        "ready": ready,
        "action": "CREATE_TOMORROW_POLL" if ready else "WAIT",
        "reasons": reasons,
    }


def print_result(result):
    print()
    print("=" * 64)
    print("D3 READINESS RECONCILIATION")
    print("=" * 64)

    print(f"home_id              : {result['home_id']}")

    if "home_name" in result:
        print(f"home_name            : {result['home_name']}")
        print(f"home_status          : {result['home_status']}")
        print(f"active_residents     : {result['active_residents']}")
        print(f"configured_residents : {result['configured_residents']}")
        print(f"tomorrow             : {result['tomorrow']}")
        print(
            f"tomorrow_poll        : "
            f"{'YES' if result['poll_exists'] else 'NONE'}"
        )

        if result["poll_id"]:
            print(f"poll_id              : {result['poll_id']}")

    print()
    print(
        f"D3 READINESS         : "
        f"{'READY' if result['ready'] else 'NOT READY'}"
    )
    print(f"ACTION               : {result['action']}")

    if result["reasons"]:
        print("REASONS              :")
        for reason in result["reasons"]:
            print(f"- {reason}")

    print("=" * 64)


async def run_reconciliation():
    meal_date = tomorrow()

    print()
    print("Starting D3 readiness reconciliation...")
    print(f"Target meal date: {meal_date}")

    home_ids = get_active_telegram_homes()

    print(
        f"Telegram-linked active Homes found: {len(home_ids)}"
    )

    results = []

    if not home_ids:
        print("No Telegram-linked Homes to reconcile.")
        return results

    for home_id in home_ids:
        try:
            result = inspect_home(home_id, meal_date)
            print_result(result)
            results.append(result)

        except Exception:
            print()
            print("=" * 64)
            print("D3 READINESS RECONCILIATION ERROR")
            print("=" * 64)
            print(f"home_id : {home_id}")
            print("reason  : READINESS_CHECK_FAILED")
            print("=" * 64)

            results.append({
                "home_id": home_id,
                "ready": False,
                "action": "WAIT",
                "reasons": ["READINESS_CHECK_FAILED"],
            })

    return results


async def main():
    print("Starting MealBot D3 Readiness Reconciler...")

    await client.start(bot_token=BOT_TOKEN)

    me = await client.get_me()
    print(f"Connected as @{me.username}")

    await run_reconciliation()

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
