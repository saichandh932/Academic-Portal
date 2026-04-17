# -*- coding: utf-8 -*-
"""
scratch/seed_and_randomize.py
-----------------------------
Seeds the MongoDB 'students' collection from 'student_credentials.csv'
and randomizes the 'email' field for all records as requested.
"""
import os
import sys
import csv
import random
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_db, init_db

def main():
    print("[Task] Initializing Database connection from .env...")
    try:
        init_db()
        db = get_db()
    except Exception as e:
        print(f"[Error] Failed to connect: {e}")
        return

    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "student_credentials.csv")
    if not os.path.exists(csv_path):
        print(f"[Error] CSV file not found at {csv_path}")
        return

    emails = [
        "chandupathuri932@gmail.com",
        "vathsavv56@gmail.com"
    ]

    print(f"[Task] Reading students from {csv_path}...")
    student_docs = []
    
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row['id']: continue
            
            # Construct document compatible with StudentModel expectations
            doc = {
                "registration_number": row['id'],
                "name": row['name'] or "Unknown",
                "email": random.choice(emails),
                "password": row['password'],
                "course": "B.Tech",
                "branch": "CSE",
                "year": 3,
                "semester": 2,
                "section": "A",
                "gender": random.choice(["Male", "Female"]),
                "dob": "2004-01-01",
                "study_hours": round(random.uniform(1.0, 10.0), 1),
                "attendance": round(random.uniform(60.0, 95.0), 1),
                "previous_score": round(random.uniform(50.0, 95.0), 1),
                "assignments": round(random.uniform(5.0, 10.0), 1),
                "internal_marks": round(random.uniform(10.0, 20.0), 1),
                "performance": random.choice(["Low", "Medium", "High"]),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            student_docs.append(doc)

    if not student_docs:
        print("[Error] No students found in CSV.")
        return

    print(f"[Task] Injecting {len(student_docs)} students into MongoDB...")
    try:
        # Clear existing to avoid unique index errors if any old data existed
        db["students"].delete_many({})
        
        # Batch insert
        result = db["students"].insert_many(student_docs)
        print(f"[Success] Successfully seeded and randomized {len(result.inserted_ids)} student records.")
        print(f"[Details] All emails set to either {emails[0]} or {emails[1]}.")
        
    except Exception as e:
        print(f"[Error] Insertion failed: {e}")

if __name__ == "__main__":
    main()
