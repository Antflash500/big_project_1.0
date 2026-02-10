import os
from dotenv import load_dotenv

# Load dari file .env di ROOT folder
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

class Config:
    # Dashboard auth
    USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
    PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin123")
    SECRET_KEY = os.getenv("WEB_SECRET_KEY", "dev_secret_key")
    
    # Bot info
    BOT_NAME = "Star Family Bot"
    BOT_COLOR = "#1a1a2e"
    
    # Database - pakai path relatif dari ROOT
    ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(ROOT_DIR, "data", "bot.db")
    
    # Print debug info
    print("=" * 50)
    print("🌟 STAR FAMILY DASHBOARD CONFIG")
    print(f"📁 Root dir: {ROOT_DIR}")
    print(f"📁 Database: {DATABASE_PATH}")
    print(f"📁 Database exists: {os.path.exists(DATABASE_PATH)}")
    print(f"🔑 Username: {USERNAME}")
    print("=" * 50)