import sys
import os

# Ensure backend package can be imported
sys.path.append(os.getcwd())

from database.db import DB, init_pool

def sync_performance():
    print("=== SYSTEM PERFORMANCE SYNCHRONIZATION ===")
    init_pool()
    
    with DB() as (conn, cur):
        # 1. Correct the column type to VARCHAR
        print("  - Hardening Schema: performance -> VARCHAR(20)")
        cur.execute("ALTER TABLE students MODIFY COLUMN performance VARCHAR(20) DEFAULT 'Low'")
        
        # 2. Reset values to 'Low' (Baseline)
        print("  - Synchronizing ranks to baseline 'Low'...")
        cur.execute("UPDATE students SET performance = 'Low'")
        
        conn.commit()
    print("[SUCCESS] System is now synchronized and ready for testing.")

if __name__ == "__main__":
    sync_performance()
