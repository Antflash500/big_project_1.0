import os
import sqlite3

print("🔍 DATABASE CHECK UTILITY")
print("=" * 50)

# Cek beberapa kemungkinan path
paths_to_check = [
    "data/bot.db",
    "./data/bot.db",
    "bot.db",
    "../data/bot.db",
    os.path.join(os.path.dirname(__file__), "data", "bot.db")
]

for path in paths_to_check:
    abs_path = os.path.abspath(path)
    exists = os.path.exists(abs_path)
    print(f"{'✅' if exists else '❌'} {abs_path}")
    
    if exists:
        try:
            conn = sqlite3.connect(abs_path)
            cursor = conn.cursor()
            
            # Cek tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            print(f"   Tables: {len(tables)}")
            for table in tables:
                print(f"     - {table[0]}")
            
            conn.close()
        except Exception as e:
            print(f"   Error: {e}")

print("=" * 50)
print("📁 Current working directory:", os.getcwd())
print("📁 Script location:", os.path.dirname(__file__))

# Coba buat database jika tidak ada
db_path = os.path.join(os.path.dirname(__file__), "data", "bot.db")
if not os.path.exists(db_path):
    print("\n🔄 Creating new database...")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.close()
    print(f"✅ Created: {db_path}")