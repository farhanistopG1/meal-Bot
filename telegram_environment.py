import asyncio

from fastapi import FastAPI

from telegram_config import API_ID, API_HASH, BOT_TOKEN

from telethon import TelegramClient


app = FastAPI(
    title="MealBot Telegram Environment Observer"
)


async def get_members(chat_id: int) -> dict:
    client = TelegramClient(
        "mealbot_observer",
        API_ID,
        API_HASH,
    )

    await client.start(bot_token=BOT_TOKEN)

    members = []

    async for user in client.iter_participants(chat_id):
        if user.bot:
            continue

        members.append(
            {
                "user_id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        )

    await client.disconnect()

    return {
        "chat_id": chat_id,
        "member_count": len(members),
        "members": members,
    }


@app.get("/environment/telegram/{chat_id}")
async def read_telegram_environment(chat_id: int):
    return await get_members(chat_id)