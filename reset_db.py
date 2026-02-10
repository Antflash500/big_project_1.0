import os
import shutil
from config import DATABASE_PATH

def reset_database():
    """Reset database completely"""
    if os.path.exists(DATABASE_PATH):
        backup = DATABASE_PATH + ".backup"
        shutil.copy2(DATABASE_PATH, backup)
        print(f"📦 Backup created: {backup}")
        os.remove(DATABASE_PATH)
        print("🗑️ Old database removed")
    
    # Recreate directory
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    # Reinitialize
    from utils.database import init_db
    init_db()
    print("✅ Database reset complete!")

if __name__ == "__main__":
    reset_database()