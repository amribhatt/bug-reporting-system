import sqlite3
import os

db_path = "bug_reports.db"

if os.path.exists(db_path):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM incidents")
        count = cursor.fetchone()[0]
        print(f"Found {count} incidents in database")
        
        if count > 0:
            cursor = conn.execute("SELECT id, user_id, level FROM incidents LIMIT 5")
            incidents = cursor.fetchall()
            print("Sample incidents:")
            for inc in incidents:
                print(f"  {inc}")
        
        # Clear all data
        conn.execute("DELETE FROM incidents")
        conn.commit()
        print("✓ Database cleared")
else:
    print("Database does not exist yet") 