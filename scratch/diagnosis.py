from database.db import DB, init_pool
import json

def diagnosis():
    init_pool()
    print("=== ATTENDANCE DATABASE DIAGNOSIS ===")
    
    with DB() as (_, cur):
        # 1. Check Locked Attendance
        print("\n[Locked Attendance Table]")
        cur.execute("SELECT * FROM locked_attendance")
        locks = cur.fetchall()
        for l in locks:
            # Format date for printing
            l['attendance_date'] = str(l['attendance_date'])
            print(f"  Slot: {l['attendance_date']} P{l['period']} | Owner: {l['subject_name']}")
            
        # 2. Check Attendance Records (Absentees only for brevity)
        print("\n[Absentees in Attendance Table]")
        cur.execute("SELECT * FROM attendance WHERE status = 'Absent'")
        absentees = cur.fetchall()
        for a in absentees:
            a['attendance_date'] = str(a['attendance_date'])
            print(f"  {a['registration_number']} | Sub: {a['subject_name']} | Date: {a['attendance_date']} | P{a['period']} | Status: {a['status']}")

        # 3. Check for any records without a period (period=1 default)
        cur.execute("SELECT count(*) as count FROM attendance WHERE period = 1")
        print(f"\n  Total records in Period 1 (Default): {cur.fetchone()['count']}")

if __name__ == "__main__":
    diagnosis()
