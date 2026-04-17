from database.db import DB, init_pool
from datetime import datetime

def deep_scan():
    init_pool()
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"--- DEEP SCAN FOR {today} ---")
    
    with DB() as (_, cur):
        # 1. Look at all locked attendance
        print("\n[Locked Attendance]")
        cur.execute("SELECT * FROM locked_attendance WHERE attendance_date = %s", (today,))
        for lock in cur.fetchall():
            print(f"  P{lock['period']} | {lock['subject_name']}")

        # 2. Count records for each period TODAY
        print("\n[Record Counts per Period]")
        cur.execute("SELECT period, count(*) as count FROM attendance WHERE attendance_date = %s GROUP BY period", (today,))
        for row in cur.fetchall():
            print(f"  Period {row['period']}: {row['count']} total student records")

        # 3. Check for any specific student entries for P6
        print("\n[Sample Data for P6]")
        cur.execute("SELECT registration_number, subject_name, status FROM attendance WHERE attendance_date = %s AND period = 6 LIMIT 5", (today,))
        for row in cur.fetchall():
            print(f"  {row['registration_number']} | {row['subject_name']} | {row['status']}")

if __name__ == "__main__":
    deep_scan()
