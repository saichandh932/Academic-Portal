from database.db import init_db, get_db
import sys

def main():
    try:
        init_db()
        db = get_db()
        student = db['students'].find_one({}, {'registration_number': 1, 'password': 1})
        if student:
            print(f"SUCCESS|{student['registration_number']}|{student['password']}")
        else:
            print("ERROR|No students found")
    except Exception as e:
        print(f"ERROR|{str(e)}")

if __name__ == "__main__":
    main()
