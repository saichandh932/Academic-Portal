import os
import sys

# Ensure backend package can be imported for Config and DB
sys.path.append(os.getcwd())

from database.db import DB, init_pool

def reset_database():
    print("=== STARTING INSTITUTIONAL DATA RESET & SCHEMA ALIGNMENT ===")
    
    # Initialize the DB Pool
    init_pool()
    
    try:
        with DB() as (conn, cur):
            # 1. SCHEMA HARDENING: Ensure all metrics columns exist in the students table
            print("  - Aligning Student Schema (Adding metrics columns if missing)...")
            metrics_cols = {
                'attendance': 'DECIMAL(5,2) DEFAULT 0.0',
                'internal_marks': 'DECIMAL(5,2) DEFAULT 0.0',
                'performance': 'DECIMAL(5,2) DEFAULT 0.0',
                'assignments': 'DECIMAL(5,2) DEFAULT 0.0'
            }
            
            for col, col_type in metrics_cols.items():
                try:
                    cur.execute(f"ALTER TABLE students ADD COLUMN {col} {col_type}")
                    print(f"    [NEW] Column {col} added successfully.")
                except Exception:
                    # Column already exists
                    pass
            
            # 2. DATA PURGE: Truncate dynamic academic records
            tables_to_clear = ['attendance', 'locked_attendance', 'student_marks', 'locked_assessments']
            for table in tables_to_clear:
                print(f"  - Purging table: {table}")
                try:
                    cur.execute(f"TRUNCATE TABLE {table}")
                except Exception as te:
                    print(f"    [WARN] Could not purge {table}: {te}")
                
            # 3. GLOBAL RESET: Zero-out all student stats
            print("  - Resetting all Student Academic metrics to 0.0...")
            cur.execute("""
                UPDATE students SET 
                    attendance = 0.0,
                    internal_marks = 0.0,
                    performance = 0.0,
                    assignments = 0.0
            """)
            
            conn.commit()
            print("\n[SUCCESS] INSTITUTIONAL RESET COMPLETE.")
            print("All academic data has been purged and students are reset to Zero.")
            
            # Verification
            cur.execute("SELECT COUNT(*) FROM students")
            print(f"[VERIFY] Registered Students remaining: {cur.fetchone()['COUNT(*)']}")
            
    except Exception as e:
        print(f"\n[ERROR] Reset Failed: {e}")

if __name__ == "__main__":
    reset_database()
