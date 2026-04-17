import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import string
import random
import csv
from database.db import DB, init_pool

def generate_password(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def migrate_db():
    print("[Migration] Initializing DB pool...")
    init_pool()

    print("[Migration] Altering students table...")
    with DB() as (conn, cur):
        try:
            cur.execute("ALTER TABLE students ADD COLUMN password VARCHAR(255) DEFAULT 'default';")
            conn.commit()
            print(" -> Added 'password' column.")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print(" -> 'password' column already exists.")
            else:
                raise e
                
    print("[Migration] Fetching all students...")
    with DB() as (conn, cur):
        cur.execute("SELECT id, name FROM students")
        students = cur.fetchall()
        
    print(f"[Migration] Generating credentials for {len(students)} students...")
    credentials = []
    
    with DB() as (conn, cur):
        for student in students:
            pw = generate_password()
            cur.execute("UPDATE students SET password = %s WHERE id = %s", (pw, student["id"]))
            credentials.append({"id": student["id"], "name": student["name"] or "Unknown", "password": pw})
        conn.commit()

    csv_path = os.path.join(os.path.dirname(__file__), "..", "student_credentials.csv")
    with open(csv_path, mode='w', newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "password"])
        writer.writeheader()
        writer.writerows(credentials)
        
    print(f"[Migration] Success. Output to {csv_path}")

if __name__ == "__main__":
    migrate_db()
