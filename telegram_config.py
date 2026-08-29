import os

from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not API_HASH or not BOT_TOKEN:
    raise RuntimeError("Telegram credentials are missing from .env")
