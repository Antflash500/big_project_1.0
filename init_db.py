import sqlite3
import os

print("🔧 INITIALIZING DATABASE...")

# Buat folder data jika belum ada
os.makedirs("data", exist_ok=True)

# Connect to database
db_path = os.path.join("data", "bot.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Buat tables
tables = [
    '''CREATE TABLE IF NOT EXISTS users (
        user_id TEXT,
        guild_id TEXT,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        messages INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, guild_id)
    )''',
    
    '''CREATE TABLE IF NOT EXISTS level_roles (
        level INTEGER,
        role_id TEXT,
        PRIMARY KEY (level)
    )''',
    
    '''CREATE TABLE IF NOT EXISTS filtered_words (
        word TEXT PRIMARY KEY
    )''',
    
    '''CREATE TABLE IF NOT EXISTS custom_commands (
        cmd_name TEXT PRIMARY KEY,
        response TEXT
    )''',
    
    '''CREATE TABLE IF NOT EXISTS confessions (
        confession_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''',
    
    '''CREATE TABLE IF NOT EXISTS welcome_config (
        guild_id TEXT PRIMARY KEY,
        channel_id TEXT
    )'''
]

for i, table_sql in enumerate(tables, 1):
    try:
        cursor.execute(table_sql)
        print(f"✅ Table {i} created")
    except Exception as e:
        print(f"⚠️ Table {i} error: {e}")

conn.commit()
conn.close()

print(f"✅ DATABASE INITIALIZED: {db_path}")
print(f"📊 Size: {os.path.getsize(db_path)} bytes")