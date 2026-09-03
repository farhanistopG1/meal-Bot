import asyncio
from datetime import datetime, timezone, timedelta

from telethon import TelegramClient, Button

from telegram_config import API_ID, API_HASH, BOT_TOKEN
import transport_database
from DCD.Project_MEALBOT.D1_HOME_MANAGEMENT import d1database as home_database


SESSION_NAME = "mealbot_resident_reconciler"

RESIDENT_SETUP_URL = "https://meal-bot.duckdns.org/configure-resident"

SCAN_INTERVAL = timedelta(days=1)


client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH,
)


def build_profile_url(chat_id, telegram_user_id, mode="resident"):
    url = (
        f"{RESIDENT_SETUP_URL}"
        f"?chat_id={chat_id}"
        f"&telegram_user_id={telegram_user_id}"
    )

    if mode == "host":
        url += "&mode=host"

    return url


def build_mention(user):
    name = user.first_name or user.username or "Resident"

    return (
        f'<a href="tg://user?id={user.id}">'
        f'{name}'
        f'</a>'
    )


async def reconcile_chat(chat_id):
    print()
    print("=" * 60)
    print("N2 RESIDENT RECONCILIATION")
    print("=" * 60)

    print(f"chat_id : {chat_id}")

    # --------------------------------------------------------
    # 1. FIND HOME
    # --------------------------------------------------------

    link = transport_database.find_telegram_home_link(
        chat_id
    )

    if link is None:
        print("No Home linked to this Telegram group.")
        print("N2 staying quiet.")
        print("=" * 60)
        return

    home_id = link["home_id"]

    print(f"home_id : {home_id}")

    home = home_database.find_home_by_id(home_id)

    if home is None:
        print("Linked Home could not be found.")
        print("=" * 60)
        return

    if not home.residents:
        print("Home has no anchor resident.")
        print("=" * 60)
        return

    host_resident = home.residents[0]

    print(
        f"host resident : "
        f"{host_resident.name} | "
        f"{host_resident.phone}"
    )

    # --------------------------------------------------------
    # 2. OBSERVE TELEGRAM GROUP
    # --------------------------------------------------------

    members = []

    async for user in client.iter_participants(chat_id):

        if getattr(user, "bot", False):
            continue

        if getattr(user, "deleted", False):
            continue

        members.append(user)

    print(f"telegram members : {len(members)}")

    # --------------------------------------------------------
    # 3. OBSERVE MEALBOT MEMORY
    # --------------------------------------------------------

    linked_user_ids = (
        transport_database.find_home_telegram_identities(
            home_id
        )
    )

    linked_user_ids = {
        int(user_id)
        for user_id in linked_user_ids
    }

    print(
        f"linked Telegram identities : "
        f"{len(linked_user_ids)}"
    )

    # --------------------------------------------------------
    # 4. RECONCILE STATE
    # --------------------------------------------------------

    matched = []
    missing = []

    for user in members:

        if user.id in linked_user_ids:
            matched.append(user)
        else:
            missing.append(user)

    # --------------------------------------------------------
    # 5. REPORT STATE
    # --------------------------------------------------------

    print()
    print(f"MATCHED : {len(matched)}")
    print(f"MISSING : {len(missing)}")

    if matched:

        print()
        print("MATCHED RESIDENTS")

        for user in matched:

            print(
                f"- {user.id} | "
                f"{user.first_name or ''} "
                f"{user.last_name or ''}"
            )

    if missing:

        print()
        print("MISSING RESIDENTS")

        for user in missing:

            print(
                f"- {user.id} | "
                f"{user.first_name or ''} "
                f"{user.last_name or ''} | "
                f"@{user.username or 'no_username'}"
            )

    # --------------------------------------------------------
    # 6. RECONCILIATION ACTION
    # --------------------------------------------------------

    for user in missing:

        mention = build_mention(user)

        telegram_name = " ".join(
            part
            for part in [
                user.first_name or "",
                user.last_name or "",
            ]
            if part
        ).strip()

        is_host = (
            telegram_name.lower()
            == host_resident.name.strip().lower()
        )

        mode = "host" if is_host else "resident"

        profile_url = build_profile_url(
            chat_id,
            user.id,
            mode=mode,
        )

        try:

            if is_host:

                await client.send_message(
                    chat_id,
                    f"{mention}, please configure your MealBot "
                    f"meal preferences.",
                    parse_mode="html",
                    buttons=[
                        [
                            Button.url(
                                "Configure Meal Preferences",
                                profile_url,
                            )
                        ]
                    ],
                )

                print(
                    f"Host preference URL sent to Telegram user "
                    f"{user.id}"
                )

            else:

                # Message 1: tag the missing resident
                await client.send_message(
                    chat_id,
                    mention,
                    parse_mode="html",
                )

                # Message 2: explain what they need to do
                await client.send_message(
                    chat_id,
                    "You are already part of this home group, "
                    "but you have not been added as a MealBot resident yet. "
                    "Please configure your MealBot profile to join your home.",
                )

                # Message 3: give them the action
                await client.send_message(
                    chat_id,
                    "Configure your MealBot profile:",
                    buttons=[
                        [Button.url("Configure MealBot", profile_url)]
                    ],
                )

                print(
                    f"Profile URL sent to Telegram user "
                    f"{user.id}"
                )

        except Exception as error:

            print(
                f"Could not message Telegram user "
                f"{user.id}: {error}"
            )

    print("=" * 60)


async def run_scan():

    linked_chats = (
        transport_database.find_active_telegram_chats()
    )

    print()
    print(
        f"Active Telegram Home links: "
        f"{len(linked_chats)}"
    )

    for chat_id in linked_chats:

        try:

            await reconcile_chat(
                int(chat_id)
            )

        except Exception as error:

            print(
                f"N2 failed for chat "
                f"{chat_id}: {error}"
            )


async def main():

    print(
        "Starting MealBot N2 Resident Reconciler..."
    )

    await client.start(
        bot_token=BOT_TOKEN,
    )

    me = await client.get_me()

    print(
        f"Connected as @{me.username}"
    )

    while True:

        print()
        print(
            f"N2 scan started at "
            f"{datetime.now(timezone.utc)}"
        )

        await run_scan()

        print()
        print(
            "N2 scan complete."
        )

        print(
            "Sleeping for 24 hours."
        )

        await asyncio.sleep(
            SCAN_INTERVAL.total_seconds()
        )


if __name__ == "__main__":
    asyncio.run(main())
