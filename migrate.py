import sqlite3
import os
from config import DATABASE_PATH

def migrate():
    """Migrate database to latest version"""
    if not os.path.exists(DATABASE_PATH):
        print("❌ Database not found!")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check and add new tables
    tables_to_add = [
        ('confession_config', '''
        CREATE TABLE confession_config (
            guild_id TEXT PRIMARY KEY,
            confession_channel TEXT,
            confession_counter INTEGER DEFAULT 0
        )
        '''),
        ('scheduled_messages', '''
        CREATE TABLE scheduled_messages (
            schedule_id TEXT PRIMARY KEY,
            guild_id TEXT,
            channel_id TEXT,
            hour INTEGER,
            minute INTEGER,
            message TEXT,
            enabled INTEGER DEFAULT 1
        )
        ''')
    ]
    
    for table_name, create_sql in tables_to_add:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            print(f"📦 Creating {table_name} table...")
            cursor.execute(create_sql)
    
    conn.commit()
    conn.close()
    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate()