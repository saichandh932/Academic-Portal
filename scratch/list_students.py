# -*- coding: utf-8 -*-
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_db, init_db

def main():
    init_db()
    db = get_db()
    students = list(db.students.find({}, {"registration_number": 1, "email": 1, "_id": 0}).sort("registration_number", 1))
    
    print(f"{'Registration Number':<25} | {'Email'}")
    print("-" * 60)
    for s in students:
        print(f"{s.get('registration_number'):<25} | {s.get('email')}")

if __name__ == "__main__":
    main()
