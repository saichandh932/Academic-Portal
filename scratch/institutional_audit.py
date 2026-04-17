import sys
import os

# Ensure backend package can be imported
sys.path.append(os.getcwd())

from database.db import DB, init_pool

def run_audit():
    print("=== INSTITUTIONAL SYSTEM INTEGRITY AUDIT ===")
    
    # Initialize the DB Pool
    init_pool()
    
    try:
        with DB() as (conn, cur):
            # 1. Attendance Audit
            print("\n[STEP 1] Checking Attendance Consistency...")
            cur.execute("""
                SELECT s.registration_number, s.attendance as stored_pct,
                       (SELECT COUNT(*) FROM attendance a WHERE a.registration_number = s.registration_number) as total,
                       (SELECT SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) FROM attendance a WHERE a.registration_number = s.registration_number) as present
                FROM students s
            """)
            drifts = 0
            students = cur.fetchall()
            for row in students:
                total = row['total'] or 0
                present = row['present'] or 0
                actual_pct = float(round((present / total * 100), 2)) if total > 0 else 0.0
                stored_pct = float(row['stored_pct'] or 0.0)
                if abs(actual_pct - stored_pct) > 0.05:
                    print(f"  [DRIFT] Student {row['registration_number']}: Stored={stored_pct}%, Actual={actual_pct}%")
                    drifts += 1
            
            if drifts == 0:
                print(f"  [SUCCESS] All Attendance records for {len(students)} students are perfectly synchronized.")
            else:
                print(f"  [ALERT] Found {drifts} students with out-of-sync attendance data.")

            # 2. Marks & Performance Audit
            print("\n[STEP 2] Checking Performance Ranking Consistency...")
            cur.execute("""
                SELECT s.registration_number, s.performance as stored_rank, s.internal_marks as stored_score,
                       (SELECT AVG((marks_obtained / max_marks) * 100) FROM student_marks m WHERE m.registration_number = s.registration_number) as avg_score
                FROM students s
            """)
            rank_errors = 0
            score_drifts = 0
            perf_data = cur.fetchall()
            for row in perf_data:
                score = float(row['avg_score'] or 0)
                actual_rank = "High" if score >= 80 else "Medium" if score >= 40 else "Low"
                
                # Check stored score drift
                if abs(score - float(row['stored_score'])) > 0.05:
                    score_drifts += 1
                
                # Check rank drift
                if row['stored_rank'] != actual_rank:
                    print(f"  [DRIFT] Student {row['registration_number']}: Stored Rank='{row['stored_rank']}', Actual='{actual_rank}' (Score={round(score,2)})")
                    rank_errors += 1
            
            if rank_errors == 0 and score_drifts == 0:
                print(f"  [SUCCESS] All Performance rankings and scores are 100% accurate.")
            elif rank_errors > 0:
                print(f"  [ALERT] Found {rank_errors} students with incorrect performance ranks.")
            elif score_drifts > 0:
                print(f"  [ALERT] Found {score_drifts} students with score-only drifts.")

            # 3. Global Locking Integrity
            print("\n[STEP 3] Verifying Institutional Global Locking...")
            cur.execute("SELECT COUNT(*) as lock_count FROM locked_attendance")
            locks = cur.fetchone()['lock_count']
            cur.execute("SELECT COUNT(DISTINCT attendance_date, period) as unique_slots FROM attendance")
            slots = cur.fetchone()['unique_slots']
            
            if locks >= slots:
                print(f"  [SUCCESS] Global Locking Shield is active. Locks: {locks}, Registered Slots: {slots}")
            else:
                print(f"  [WARN] Data Integrity Risk: Fewer locks ({locks}) than slots ({slots}) found.")

    except Exception as e:
        print(f"\n[ERROR] Audit Failed: {e}")

if __name__ == "__main__":
    run_audit()
