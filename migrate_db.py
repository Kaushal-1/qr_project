#!/usr/bin/env python3
import sqlite3
import config

def migrate_database():
    """Add new columns to existing database"""
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Add new columns if they don't exist
        cursor.execute("ALTER TABLE scans ADD COLUMN phash_distance INTEGER")
        print("Added phash_distance column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("phash_distance column already exists")
        else:
            print(f"Error adding phash_distance: {e}")
    
    try:
        cursor.execute("ALTER TABLE scans ADD COLUMN orb_ratio REAL")
        print("Added orb_ratio column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("orb_ratio column already exists")
        else:
            print(f"Error adding orb_ratio: {e}")
    
    conn.commit()
    conn.close()
    print("Database migration complete!")

if __name__ == "__main__":
    migrate_database()