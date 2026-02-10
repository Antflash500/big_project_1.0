import subprocess
import sys
import os
import time
from threading import Thread

def run_bot():
    print("🤖 Starting Discord Bot...")
    subprocess.run([sys.executable, "main.py"])

def run_dashboard():
    print("🌐 Starting Web Dashboard...")
    os.chdir("web")
    subprocess.run([sys.executable, "run.py"])

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 STAR FAMILY BOT SYSTEM")
    print("=" * 50)
    
    # Initialize database
    print("\n🔧 Initializing database...")
    subprocess.run([sys.executable, "init_db.py"])
    
    # Run in threads
    bot_thread = Thread(target=run_bot, daemon=True)
    dashboard_thread = Thread(target=run_dashboard, daemon=True)
    
    bot_thread.start()
    time.sleep(3)
    dashboard_thread.start()
    
    # Keep script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")