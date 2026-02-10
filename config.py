import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!")
BOT_COLOR = int(os.getenv("BOT_COLOR", "0x1a1a2e"), 16)

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/bot.db")

print("=" * 50)
print("🌐 NEXUS COMMUNITY BOT CONFIGURATION")
print(f"🔑 Bot: {PREFIX} commands")
print(f"🎨 Color: {hex(BOT_COLOR)}")
print(f"📁 Database: {DATABASE_PATH}")
print("=" * 50)