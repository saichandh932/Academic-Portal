# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import DB, init_pool

def heal():
    print("LOG: Starting Institutional Normalization Sweep")
    init_pool()
    
    normalization_map = {
        "CNS-L": "CNS Lab",
        "library": "Library",
        "TRg": "Training (TRG)"
    }
    
    with DB() as (conn, cur):
        print("LOG: Ensuring schema alignment")
        cur.execute("SHOW COLUMNS FROM students LIKE 'name'")
        if not cur.fetchone():
            print("LOG: Adding missing 'name' column to students")
            cur.execute("ALTER TABLE students ADD COLUMN name VARCHAR(100) DEFAULT 'Unknown' AFTER registration_number")
            conn.commit()

        print("LOG: Updating Student Names")
        cur.execute("UPDATE students SET name = CONCAT('Student ', registration_number) WHERE name = 'Unknown' OR name IS NULL OR name = ''")
        print("OK: Student name updates complete")

        print("LOG: Updating Subject Codes")
        for old, new in normalization_map.items():
            cur.execute("UPDATE student_marks SET subject_name = %s WHERE subject_name = %s", (new, old))
            cur.execute("UPDATE attendance SET subject_name = %s WHERE subject_name = %s", (new, old))
            cur.execute("UPDATE locked_attendance SET subject_name = %s WHERE subject_name = %s", (new, old))
            cur.execute("UPDATE locked_assessments SET subject_name = %s WHERE subject_name = %s", (new, old))
            cur.execute("UPDATE admins SET assigned_subject = %s WHERE assigned_subject = %s", (new, old))
        print("OK: Subject code migration complete")

        print("LOG: Syncing Performance Logic")
        cur.execute("UPDATE student_marks SET performance_status = 'Low' WHERE performance_status = 'Below Threshold'")
        
        conn.commit()
    print("COMPLETE: Institutional healing finished")

if __name__ == "__main__":
    heal()
