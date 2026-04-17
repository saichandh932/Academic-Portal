# -*- coding: utf-8 -*-
"""
scratch/heal_institutional_names.py
-----------------------------------
Institutional Healing Script:
1. Normalizes Subject Names across all tables (Attendance, Marks, Locks, Admins).
2. Fixes student names by replacing 'Unknown' with 'Student [Reg#]'.
"""
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import DB, init_pool

def heal():
    print("[HEAL] Starting Institutional Normalization Sweep...")
    init_pool()
    
    normalization_map = {
        "CNS-L": "CNS Lab",
        "library": "Library",
        "TRg": "Training (TRG)"
    }
    
    with DB() as (conn, cur):
        # 1. Update Students Registry
        print("[HEAL] Polishing Student Identity Registry...")
        cur.execute("""
            UPDATE students 
            SET name = CONCAT('Student ', registration_number) 
            WHERE name = 'Unknown' OR name IS NULL OR name = ''
        """)
        print(f"  --> Identified and polished {cur.rowcount} student names.")

        # 2. Update Student Marks
        print("[HEAL] Migrating Assessment Marks Subject Codes...")
        for old, new in normalization_map.items():
            cur.execute("UPDATE student_marks SET subject_name = %s WHERE subject_name = %s", (new, old))
            if cur.rowcount > 0:
                print(f"  --> Migrated {cur.rowcount} records from '{old}' to '{new}' in student_marks.")

        # 3. Update Attendance
        print("[HEAL] Migrating Attendance Registry Subject Codes...")
        for old, new in normalization_map.items():
            cur.execute("UPDATE attendance SET subject_name = %s WHERE subject_name = %s", (new, old))
            if cur.rowcount > 0:
                print(f"  --> Migrated {cur.rowcount} records from '{old}' to '{new}' in attendance.")

        # 4. Update Locks
        print("[HEAL] Migrating Institutional Security Locks...")
        for old, new in normalization_map.items():
            cur.execute("UPDATE locked_attendance SET subject_name = %s WHERE subject_name = %s", (new, old))
            if cur.rowcount > 0:
                print(f"  --> Migrated {cur.rowcount} attendance locks from '{old}' to '{new}'.")
            
            cur.execute("UPDATE locked_assessments SET subject_name = %s WHERE subject_name = %s", (new, old))
            if cur.rowcount > 0:
                print(f"  --> Migrated {cur.rowcount} assessment locks from '{old}' to '{new}'.")

        # 5. Update Admin Assignments
        print("[HEAL] Aligning Administrator Roles...")
        for old, new in normalization_map.items():
            cur.execute("UPDATE admins SET assigned_subject = %s WHERE assigned_subject = %s", (new, old))
            if cur.rowcount > 0:
                print(f"  --> Re-assigned {cur.rowcount} administrators from '{old}' to '{new}'.")

        # 6. Normalize Global Status
        print("[HEAL] Synchronizing Performance Logic (Below Threshold -> Low)...")
        cur.execute("UPDATE student_marks SET performance_status = 'Low' WHERE performance_status = 'Below Threshold'")
        if cur.rowcount > 0:
            print(f"  --> Synchronized {cur.rowcount} performance status labels.")

        conn.commit()
        print("\n[HEAL] INSTITUTIONAL HEALING COMPLETE. Data is now synchronized and polished.")

if __name__ == "__main__":
    try:
        heal()
    except Exception as e:
        print(f"[ERROR] Healing sequence failed: {e}")
        sys.exit(1)
