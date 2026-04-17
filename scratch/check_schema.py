import sys, os
sys.path.append(os.getcwd())
from database.db import DB, init_pool
import json

def check():
    init_pool()
    with DB() as (conn, cur):
        cur.execute("DESCRIBE students")
        students_cols = cur.fetchall()
        print("COLUMNS IN students:")
        print(json.dumps(students_cols, indent=2))

        cur.execute("SELECT * FROM students LIMIT 1")
        sample = cur.fetchone()
        print("\nSAMPLE ROW:")
        print(json.dumps(sample, indent=2, default=str))

if __name__ == "__main__":
    check()
