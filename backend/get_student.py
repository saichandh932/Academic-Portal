import sys
import os
sys.path.append(os.getcwd())
from database.db import init_db, get_db

def run():
    init_db('mongodb://localhost:27017', 'student_db')
    db = get_db()
    s = db['students'].find_one({}, {'registration_number': 1, 'password': 1})
    if s:
        print(f"ID: {s['registration_number']}")
        print(f"PASS: {s['password']}")
    else:
        print("No students found.")

if __name__ == "__main__":
    run()
