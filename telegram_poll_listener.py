import asyncio
from datetime import datetime, timezone

from telethon import TelegramClient, events, types

from telegram_config import API_ID, API_HASH, BOT_TOKEN


SESSION_NAME = "mealbot_poll_listener"

HOST_POLL_QUESTION = "Who should be the Home host?"

# TEMPORARY:
# Replace this with the actual Home configuration page
# once that page/API is ready.
HOST_SETUP_URL = "https://meal-bot.duckdns.org/configure"

client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH,
)

tracked_polls = {}
processed_polls = set()
processing_polls = set()


def text_value(value):
    if hasattr(value, "text"):
        return value.text

    return str(value)


def build_poll_options(poll):
    return [
        text_value(answer.text)
        for answer in poll.answers
    ]


def find_winner(poll):
    results = getattr(poll, "results", None)

    if results is None:
        return None

    ranked = []

    for answer, result in zip(
        poll.poll.answers,
        results.results or [],
    ):
        ranked.append(
            (
                result.voters or 0,
                text_value(answer.text),
            )
        )

    if not ranked:
        return None

    ranked.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return ranked[0]


async def create_host_poll(
    peer,
    chat_id,
    options,
):
    """
    Create a fresh host-selection poll using Telegram Bot API.
    """

    import json
    import urllib.request

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"

    payload = {
        "chat_id": chat_id,
        "question": HOST_POLL_QUESTION,
        "options": json.dumps(options),
        "is_anonymous": False,
        "open_period": 60,
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

    return await client.get_messages(
        peer,
        ids=message_id,
    )


async def process_closed_poll(poll_id):

    if poll_id in processed_polls:
        return

    if poll_id in processing_polls:
        return

    processing_polls.add(poll_id)

    poll_info = tracked_polls.get(poll_id)

    if poll_info is None:
        processing_polls.discard(poll_id)
        return

    close_date = poll_info["close_date"]

    now = datetime.now(timezone.utc)

    wait_seconds = max(
        0,
        (close_date - now).total_seconds(),
    )

    if wait_seconds:
        print(
            f"Poll {poll_id} closes in "
            f"{wait_seconds:.1f} seconds."
        )

        await asyncio.sleep(
            wait_seconds + 2
        )

    if poll_id in processed_polls:
        return

    try:
        message = await client.get_messages(
            poll_info["peer"],
            ids=poll_info["message_id"],
        )

    except Exception as error:
        print(
            f"Could not retrieve poll {poll_id}: {error}"
        )
        return

    if message is None:
        print(
            f"Poll {poll_id} message not found."
        )
        return

    if not isinstance(
        message.media,
        types.MessageMediaPoll,
    ):
        print(
            f"Poll {poll_id} is not a poll anymore."
        )
        return

    final_poll = message.media

    poll = final_poll.poll

    if not getattr(
        poll,
        "closed",
        False,
    ):
        print(
            f"Poll {poll_id} is not closed yet."
        )
        return

    processed_polls.add(poll_id)
    processing_polls.discard(poll_id)

    winner = find_winner(
        final_poll
    )

    print()
    print("=" * 60)
    print("HOST POLL CLOSED")
    print("=" * 60)

    print(
        f"poll_id : {poll_id}"
    )

    if winner is None:
        print(
            "NO RESULT"
        )
        print("=" * 60)
        return

    winner_name, vote_count = (
        winner[1],
        winner[0],
    )

    print(
        f"winner  : {winner_name}"
    )

    print(
        f"votes   : {vote_count}"
    )

    # --------------------------------------------------------
    # NO VOTES
    # --------------------------------------------------------

    if vote_count == 0:

        print(
            "Nobody voted. Creating the poll again."
        )

        new_message = await create_host_poll(
            poll_info["peer"],
            poll_info["chat_id"],
            poll_info["options"],
        )

        new_poll = new_message.media.poll

        new_poll_id = new_poll.id

        new_close_date = new_poll.close_date

        tracked_polls[new_poll_id] = {
            "peer": poll_info["peer"],
            "message_id": new_message.id,
            "close_date": new_close_date,
            "options": poll_info["options"],
        }

        print(
            f"New host poll created: {new_poll_id}"
        )

        asyncio.create_task(
            process_closed_poll(
                new_poll_id
            )
        )

        print("=" * 60)

        return

    # --------------------------------------------------------
    # WINNER
    # --------------------------------------------------------

    print()
    print(
        f"{winner_name} has been selected as the Home host."
    )

    await client.send_message(
        poll_info["peer"],
        (
            f"🎉 {winner_name} has been selected "
            f"as the Home host!\n\n"
            f"{winner_name}, please open this link "
            f"to configure the MealBot Home:\n"
            f"{HOST_SETUP_URL}?chat_id={poll_info['chat_id']}"
        ),
    )

    print(
        "Host announcement sent to Telegram."
    )

    print("=" * 60)


@client.on(events.NewMessage)
async def new_message_listener(event):

    message = event.message

    if not isinstance(
        message.media,
        types.MessageMediaPoll,
    ):
        return

    poll = message.media.poll

    question = text_value(
        poll.question
    )

    if question != HOST_POLL_QUESTION:
        return

    close_date = poll.close_date

    if close_date is None:
        return

    poll_id = poll.id

    options = build_poll_options(
        poll
    )

    tracked_polls[poll_id] = {
        "peer": await event.get_input_chat(),
        "chat_id": event.chat_id,
        "message_id": message.id,
        "close_date": close_date,
        "options": options,
    }

    print()
    print("=" * 60)
    print("HOST POLL DETECTED")
    print("=" * 60)

    print(
        f"poll_id : {poll_id}"
    )

    print(
        f"chat_id : {event.chat_id}"
    )

    print(
        f"message : {message.id}"
    )

    print(
        f"options : {options}"
    )

    print(
        f"closes  : {close_date}"
    )

    print("=" * 60)

    asyncio.create_task(
        process_closed_poll(
            poll_id
        )
    )


async def main():

    print(
        "Starting MealBot Telegram Poll Listener..."
    )

    await client.start(
        bot_token=BOT_TOKEN,
    )

    me = await client.get_me()

    print(
        f"Connected as @{me.username}"
    )

    print(
        "Listening for host-selection polls..."
    )

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
