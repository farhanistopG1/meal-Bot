import asyncio
import json
import urllib.request

from telethon import TelegramClient, events, types

from telegram_config import API_ID, API_HASH, BOT_TOKEN

import transport_database

from DCD.Project_MEALBOT.D3_Daily_Meal_Coordination import d3database
from organs import vote_on_daily_meal_poll


SESSION_NAME = "mealbot_d3_poll_reconciler"


client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH,
)


async def create_telegram_meal_poll(
    chat_id,
    poll,
):
    """Create the external Telegram representation of a D3 poll."""
    url = "https://" + "api.telegram.org" + "/bot" + BOT_TOKEN + "/sendPoll"

    payload = {
        "chat_id": chat_id,
        "question": (
            f"What should we have for "
            f"{poll.meal_date}?"
        ),
        "options": json.dumps(
            list(poll.options)
        ),
        "is_anonymous": False,
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

    response = await asyncio.to_thread(
        urllib.request.urlopen,
        request,
    )

    response_data = json.loads(
        response.read().decode()
    )

    if not response_data.get("ok"):
        raise RuntimeError(
            f"Telegram sendPoll failed: {response_data}"
        )

    message_id = response_data["result"]["message_id"]

    message = await client.get_messages(
        chat_id,
        ids=message_id,
    )

    return message


async def stop_telegram_meal_poll(chat_id, message_id):
    """Stop the external Telegram representation of a D3 poll."""
    url = "https://" + "api.telegram.org" + "/bot" + BOT_TOKEN + "/stopPoll"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
    }
    data = json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    response = await asyncio.to_thread(
        urllib.request.urlopen,
        request,
    )
    response_data = json.loads(response.read().decode())

    if not response_data.get("ok"):
        raise RuntimeError(
            f"Telegram stopPoll failed: {response_data}"
        )

    return response_data["result"]


async def reconcile():
    """Reconcile D3 poll state with Telegram transport."""
    polls = d3database.list_polls()

    for poll in polls:
        if poll.status not in ("Open", "Closed"):
            continue

        binding = transport_database.find_binding_by_daily_meal_poll(
            poll.id
        )

        print(
            f"D3 poll {poll.id} | "
            f"date={poll.meal_date} | "
            f"status={poll.status} | "
            f"binding={'YES' if binding else 'NO'}"
        )

        if poll.status == "Closed":
            if binding is None:
                print(
                    f"Closed D3 poll {poll.id} has no Telegram binding"
                )
                continue

            if binding["closed_at"] is not None:
                continue

            if binding["provider_message_id"] is None:
                print(
                    f"Cannot stop Telegram poll for D3 poll {poll.id}: "
                    "provider_message_id is missing"
                )
                continue

            endpoint = (
                transport_database.find_active_home_telegram_endpoint(
                    poll.home.id
                )
            )

            if endpoint is None:
                print(
                    f"No active Telegram endpoint for Home "
                    f"{poll.home.id}"
                )
                continue

            chat_id = int(
                endpoint["external_destination_id"]
            )

            await stop_telegram_meal_poll(
                chat_id,
                int(binding["provider_message_id"]),
            )

            transport_database.close_poll_binding(
                poll.id
            )

            print(
                f"Telegram poll stopped | "
                f"D3 poll={poll.id}"
            )

            continue

        if binding:
            continue

        endpoint = (
            transport_database.find_active_home_telegram_endpoint(
                poll.home.id
            )
        )

        if endpoint is None:
            print(
                f"No active Telegram endpoint for Home "
                f"{poll.home.id}"
            )
            continue

        endpoint_id = endpoint["id"]
        chat_id = int(
            endpoint["external_destination_id"]
        )

        print(
            f"Telegram destination : {chat_id}"
        )

        message = await create_telegram_meal_poll(
            chat_id,
            poll,
        )

        telegram_poll_id = message.media.poll.id
        telegram_message_id = message.id

        print(
            f"Telegram poll created : {telegram_poll_id}"
        )

        transport_database.create_poll_binding(
            home_id=poll.home.id,
            daily_meal_poll_id=poll.id,
            transport_endpoint_id=endpoint_id,
            provider_poll_id=str(telegram_poll_id),
            provider_message_id=str(telegram_message_id),
        )

        print(
            f"Binding created for D3 poll {poll.id}"
        )

@client.on(events.Raw(types=types.UpdateMessagePollVote))
async def poll_vote_listener(update):
    """Translate a live Telegram vote into a D3 MealVote."""
    binding = transport_database.find_binding_by_provider_poll_id(
        str(update.poll_id)
    )

    if binding is None:
        return

    if not update.positions:
        return

    resident = transport_database.find_resident_by_telegram_identity(
        update.peer.user_id
    )

    if resident is None:
        print(
            f"Unknown Telegram resident: {update.peer.user_id}"
        )
        return

    poll = d3database.find_poll_by_id(
        binding["daily_meal_poll_id"]
    )

    if poll is None:
        print(
            f"D3 poll not found: {binding['daily_meal_poll_id']}"
        )
        return

    position = update.positions[0]

    if position < 0 or position >= len(poll.options):
        print(
            f"Invalid Telegram poll position: {position}"
        )
        return

    selected_meal = poll.options[position]

    vote_on_daily_meal_poll(
        resident_phone=resident["phone"],
        meal_date=poll.meal_date,
        selected_meal=selected_meal,
    )

    print(
        f"D3 vote recorded | "
        f"resident={resident['name']} | "
        f"meal={selected_meal}"
    )


async def main():
    print(
        "Starting MealBot Telegram D3 Poll Reconciler..."
    )

    await client.start(
        bot_token=BOT_TOKEN,
    )

    me = await client.get_me()

    print(
        f"Connected as @{me.username}"
    )


    while True:
        await reconcile()
        await asyncio.sleep(60)



if __name__ == "__main__":
    asyncio.run(main())
