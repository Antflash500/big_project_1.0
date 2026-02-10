import sqlite3
import os
from config import DATABASE_PATH

def get_db_path():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    return DATABASE_PATH

def init_db():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # DROP OLD TABLES FIRST
    cursor.execute("DROP TABLE IF EXISTS confession_config")
    
    # CREATE ALL TABLES
    tables = [
        # Users table (leveling)
        ('''CREATE TABLE IF NOT EXISTS users (
            user_id TEXT,
            guild_id TEXT,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            messages INTEGER DEFAULT 0,
            last_message_time TIMESTAMP,
            PRIMARY KEY (user_id, guild_id)
        )'''),
        
        # Level roles
        ('''CREATE TABLE IF NOT EXISTS level_roles (
            guild_id TEXT,
            level INTEGER,
            role_id TEXT,
            PRIMARY KEY (guild_id, level)
        )'''),
        
        # Filtered words
        ('''CREATE TABLE IF NOT EXISTS filtered_words (
            guild_id TEXT,
            word TEXT,
            added_by TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (guild_id, word)
        )'''),
        
        # Custom commands
        ('''CREATE TABLE IF NOT EXISTS custom_commands (
            guild_id TEXT,
            cmd_name TEXT,
            response TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (guild_id, cmd_name)
        )'''),
        
        # Confession setup (NEW)
        ('''CREATE TABLE IF NOT EXISTS confession_setup (
            guild_id TEXT PRIMARY KEY,
            confession_channel_id TEXT,
            log_channel_id TEXT,
            user_log_channel_id TEXT,
            current_number INTEGER DEFAULT 0,
            setup_message_id TEXT
        )'''),
        
        # Dalam fungsi init_db(), update tabel confession_messages:

        # Confession messages (UPDATED)
        ('''CREATE TABLE IF NOT EXISTS confession_messages (
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
        )'''),
        
        # Welcome config
        ('''CREATE TABLE IF NOT EXISTS welcome_config (
            guild_id TEXT PRIMARY KEY,
            channel_id TEXT,
            welcome_message TEXT DEFAULT 'Welcome {member} to {server}!',
            goodbye_message TEXT DEFAULT 'Goodbye {member}!'
        )'''),
        
        # Scheduled messages (NEW)
        ('''CREATE TABLE IF NOT EXISTS scheduled_messages (
            schedule_id TEXT PRIMARY KEY,
            guild_id TEXT,
            channel_id TEXT,
            hour INTEGER,
            minute INTEGER,
            message TEXT,
            enabled INTEGER DEFAULT 1
        )''')
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

def execute_query(query, params=(), fetch=False, fetchall=False, commit=True):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params)
        
        if fetch:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
        else:
            result = cursor.rowcount
        
        if commit:
            conn.commit()
        return result
    except Exception as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

# 🔥 Fungsi baru untuk migrasi
def migrate_db():
    """Migrate old database if needed"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    try:
        # Cek apakah tabel users punya primary key lama
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        has_primary = any(col[5] == 1 for col in columns)  # col[5] is pk
        
        if not has_primary:
            print("🔄 Migrating users table...")
            # Backup data
            cursor.execute("SELECT * FROM users")
            old_data = cursor.fetchall()
            
            # Drop and recreate with new schema
            cursor.execute("DROP TABLE users")
            cursor.execute('''
            CREATE TABLE users (
                user_id TEXT,
                guild_id TEXT,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                messages INTEGER DEFAULT 0,
                last_message_time TIMESTAMP,
                PRIMARY KEY (user_id, guild_id)
            )
            ''')

            # Tabel confession config
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS confession_config (
                guild_id TEXT PRIMARY KEY,
                confession_channel TEXT,
                confession_counter INTEGER DEFAULT 0
            )
            ''')

            # Tabel scheduled messages
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_messages (
                schedule_id TEXT PRIMARY KEY,
                guild_id TEXT,
                channel_id TEXT,
                hour INTEGER,
                minute INTEGER,
                message TEXT,
                enabled INTEGER DEFAULT 1
            )
            ''')

            # Tabel confession setup
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS confession_setup (
                guild_id TEXT PRIMARY KEY,
                confession_channel_id TEXT,
                log_channel_id TEXT,
                user_log_channel_id TEXT,
                current_number INTEGER DEFAULT 0,
                setup_message_id TEXT
            )
            ''')

            # Tabel confession messages
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS confession_messages (
                confession_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT,
                user_id TEXT,
                message TEXT,
                confession_number INTEGER,
                thread_id TEXT,
                message_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                replies_count INTEGER DEFAULT 0
            )
            ''')

            # Insert old data dengan guild_id default
            for row in old_data:
                if len(row) >= 2:
                    cursor.execute(
                        "INSERT INTO users (user_id, guild_id, xp, level, messages) VALUES (?, 'default', ?, ?, ?)",
                        row[:4]
                    )
            
            conn.commit()
            print("✅ Migration complete")
    except Exception as e:
        print(f"⚠️ Migration skipped: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    migrate_db()
    print("✅ Database setup complete")