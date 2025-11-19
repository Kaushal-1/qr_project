#!/usr/bin/env python3
import sqlite3
import config

def reset_demo():
    """Reset database for clean demo"""
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    # Clear all scans
    cursor.execute("DELETE FROM scans")
    
    # Remove SERFake (keep only SERGenuine for demo)
    cursor.execute("DELETE FROM items WHERE serial = 'SERFake'")
    
    # Show remaining items
    cursor.execute("SELECT serial, product, batch FROM items")
    items = cursor.fetchall()
    
    conn.commit()
    conn.close()
    
    print("Database reset for demo!")
    print("Remaining items:")
    for item in items:
        print(f"  - {item[0]} ({item[1]}, {item[2]})")
    print("\nNow:")
    print("- SERGenuine will show AUTHENTIC")
    print("- SERFake will show NOT AUTHENTIC (unknown_serial)")

if __name__ == "__main__":
    reset_demo()