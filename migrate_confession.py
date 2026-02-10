# File `migrate_clean.py`
import sqlite3
import os
from config import DATABASE_PATH

def migrate_clean():
    """Migrate to clean confession system"""
    if not os.path.exists(DATABASE_PATH):
        print("❌ Database not found!")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("🔄 Migrating to clean confession system...")
    
    # Ensure tables exist with correct schema
    tables = [
        '''CREATE TABLE IF NOT EXISTS confession_setup (
            guild_id TEXT PRIMARY KEY,
            confession_channel_id TEXT,
            log_channel_id TEXT,
            user_log_channel_id TEXT,
            current_number INTEGER DEFAULT 0,
            setup_message_id TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS confession_messages (
            confession_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            user_id TEXT,
            message TEXT,
            confession_number INTEGER,
            thread_id TEXT,
            message_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            replies_count INTEGER DEFAULT 0,
            is_reply INTEGER DEFAULT 0,
            reply_to INTEGER
        )'''
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)
    
    conn.commit()
    conn.close()
    print("✅ Clean migration complete!")

if __name__ == "__main__":
    migrate_clean()