# -*- coding: utf-8 -*-
"""
scratch/randomize_student_emails.py
----------------------------------
Helper script to randomize all student emails using the provided test addresses.
Takes connection details from the .env via the application's config layer.
"""
import os
import sys
import random

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_db, init_db

def main():
    print("[Task] Initializing database connection...")
    try:
        # init_db will use Config (loaded from .env)
        init_db()
        db = get_db()
        
        emails = [
            "chandupathuri932@gmail.com",
            "vathsavv56@gmail.com"
        ]
        
        students_col = db["students"]
        all_students = list(students_col.find({}, {"registration_number": 1}))
        
        print(f"[Task] Found {len(all_students)} students to update.")
        
        updated_count = 0
        for student in all_students:
            reg_id = student["registration_number"]
            new_email = random.choice(emails)
            
            result = students_col.update_one(
                {"registration_number": reg_id},
                {"$set": {"email": new_email}}
            )
            
            if result.modified_count > 0:
                updated_count += 1
        
        print(f"[Success] Updated {updated_count} students with randomized test emails.")
        
    except Exception as e:
        print(f"[Error] Failed to update emails: {e}")

if __name__ == "__main__":
    main()
