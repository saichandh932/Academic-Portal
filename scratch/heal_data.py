from database.db import DB, init_pool
from datetime import datetime

def heal_attendance():
    init_pool()
    print("=== ATTENDANCE DATA HEALING START ===")
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    with DB() as (conn, cur):
        # 1. Look for 'ML' records for today that might be in the wrong period
        print(f"[1] Checking 'ML' records for {today}...")
        cur.execute("SELECT count(*) as count, period FROM attendance WHERE subject_name = 'ML' AND attendance_date = %s GROUP BY period", (today,))
        stats = cur.fetchall()
        for s in stats:
            print(f"    Found {s['count']} records in Period {s['period']}")

        # 2. Check if there's a lock for ML in P7
        cur.execute("SELECT * FROM locked_attendance WHERE subject_name = 'ML' AND attendance_date = %s", (today,))
        lock = cur.fetchone()
        if lock:
            print(f"[2] Found ML Lock for {today} in Period {lock['period']}")
            
            # 3. HEAL: If records are in Period 1 but Lock is in Period 7, MOVE them.
            # (Or if user intended them to be in P7 but they defaulted to 1)
            target_period = 7 
            print(f"[3] Moving all ML records for today to Period {target_period}...")
            cur.execute("""
                UPDATE attendance 
                SET period = %s 
                WHERE subject_name = 'ML' AND attendance_date = %s AND period != %s
            """, (target_period, today, target_period))
            moved = cur.rowcount
            print(f"    Successfully moved {moved} records to Period {target_period}.")
            
            # 4. Ensure the lock is also correct
            cur.execute("""
                UPDATE locked_attendance 
                SET period = %s 
                WHERE subject_name = 'ML' AND attendance_date = %s
            """, (target_period, today))
            
            conn.commit()
            print("[4] Database synchronized.")
        else:
            print("[2] No ML lock found for today. Searching for ANY locked period today...")
            cur.execute("SELECT * FROM locked_attendance WHERE attendance_date = %s", (today,))
            other_lock = cur.fetchone()
            if other_lock:
                print(f"    Found lock by {other_lock['subject_name']} in Period {other_lock['period']}.")

if __name__ == "__main__":
    heal_attendance()
