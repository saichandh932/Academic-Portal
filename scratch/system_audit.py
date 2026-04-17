import mysql.connector
from backend.config import Config
import json

def system_audit():
    print("=== STARTING SYSTEMATIC INTEGRATION AUDIT ===")
    
    # ── 1. Database Connection Check ──────────────────────────────────────────
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=Config.DB_PORT
        )
        cur = conn.cursor(dictionary=True)
        print("[PASS] Database Connection Successful.")
    except Exception as e:
        print(f"[FAIL] Database Connection: {e}")
        return

    # ── 2. Schema Verification ────────────────────────────────────────────────
    print("\n[Audit] Verifying Schema Consistency...")
    tables = ['attendance', 'locked_attendance', 'students']
    for t in tables:
        cur.execute(f"DESCRIBE {t}")
        cols = [c['Field'] for c in cur.fetchall()]
        print(f"  - Table '{t}': {', '.join(cols)}")
        
        if t == 'attendance' and 'period' not in cols:
            print(f"    [ERROR] Missing 'period' column in {t}")
        if t == 'locked_attendance' and 'period' not in cols:
            print(f"    [ERROR] Missing 'period' column in {t}")

    # ── 3. Unique Index Check (Global Locking) ────────────────────────────────
    print("\n[Audit] Verifying Unique Constraints (Integrity)...")
    cur.execute("SHOW INDEX FROM locked_attendance")
    indexes = [i['Key_name'] for i in cur.fetchall()]
    if 'uc_lock' in indexes:
        print("  [PASS] Global Lock Index (uc_lock) is active.")
    else:
        print("  [FAIL] Global Lock Index (uc_lock) is MISSING. System may allow duplicates.")

    # ── 4. Cross-Subject Synchronization Logic ────────────────────────────────
    print("\n[Audit] Verifying Data Synchronization Logic...")
    # Checking for any "Orphaned" locks (locks without a subject or date)
    cur.execute("SELECT count(*) as count FROM locked_attendance WHERE subject_name IS NULL OR attendance_date IS NULL")
    orphans = cur.fetchone()['count']
    if orphans == 0:
        print("  [PASS] No orphaned locks found.")
    else:
        print(f"  [FAIL] Found {orphans} orphaned locks. This will cause dashboard errors.")

    # ── 5. Percentage Logic Audit ────────────────────────────────────────────
    print("\n[Audit] Verifying Calculation Logic...")
    cur.execute("SELECT registration_number, attendance FROM students LIMIT 1")
    sample = cur.fetchone()
    if sample:
        print(f"  Sample Student: {sample['registration_number']} | Global Attendance: {sample['attendance']}%")
        # Validate against actual records
        cur.execute("SELECT count(*) as total, SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present FROM attendance WHERE registration_number = %s", (sample['registration_number'],))
        stats = cur.fetchone()
        real_calc = round((stats['present'] / stats['total']) * 100, 2) if stats['total'] > 0 else 0.0
        if abs(float(sample['attendance']) - real_calc) < 0.1:
            print(f"  [PASS] Live Percentage Engine is Accurate (Real: {real_calc}%, DB: {sample['attendance']}%)")
        else:
             print(f"  [WARNING] Percentage Mismatch for {sample['registration_number']}. Engine may need force-sync.")

    conn.close()
    print("\n=== AUDIT COMPLETE ===")

if __name__ == "__main__":
    system_audit()
