import os
import sqlite3
import sys

def fix_database():
    print("🛠️  DATABASE FIXER")
    print("=" * 50)
    
    # Tentukan path database
    script_dir = os.path.dirname(__file__)
    db_path = os.path.join(script_dir, "data", "bot.db")
    
    print(f"📁 Script directory: {script_dir}")
    print(f"📁 Database path: {db_path}")
    
    # Buat folder data jika belum ada
    data_dir = os.path.dirname(db_path)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"✅ Created directory: {data_dir}")
    
    # Buat database baru
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Buat semua tables
        tables = [
            '''CREATE TABLE IF NOT EXISTS users (
                user_id TEXT,
                guild_id TEXT,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                messages INTEGER DEFAULT 0,
                last_message_time TIMESTAMP,
                PRIMARY KEY (user_id, guild_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS level_roles (
                level INTEGER,
                role_id TEXT,
                PRIMARY KEY (level)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS filtered_words (
                word TEXT PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            
            '''CREATE TABLE IF NOT EXISTS custom_commands (
                cmd_name TEXT PRIMARY KEY,
                response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            
            '''CREATE TABLE IF NOT EXISTS confessions (
                confession_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            
            '''CREATE TABLE IF NOT EXISTS welcome_config (
                guild_id TEXT PRIMARY KEY,
                channel_id TEXT
            )'''
        ]
        
        for table_sql in tables:
            try:
                cursor.execute(table_sql)
                print(f"✅ Table created/checked")
            except Exception as e:
                print(f"⚠️ Warning: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Database fixed successfully!")
        print(f"📊 Location: {db_path}")
        print(f"📊 Size: {os.path.getsize(db_path)} bytes")
        
        # Update .env file
        env_path = os.path.join(script_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                content = f.read()
            
            # Update DATABASE_PATH
            if "DATABASE_PATH=" in content:
                new_content = []
                for line in content.split('\n'):
                    if line.startswith("DATABASE_PATH="):
                        new_content.append(f"DATABASE_PATH={db_path}")
                    else:
                        new_content.append(line)
                
                with open(env_path, 'w') as f:
                    f.write('\n'.join(new_content))
                print("✅ Updated .env file with absolute path")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if fix_database():
        print("\n🎉 Fix completed! Restart your dashboard.")
        print("👉 Run: cd web && python app.py")
    else:
        print("\n❌ Fix failed!")
        sys.exit(1)