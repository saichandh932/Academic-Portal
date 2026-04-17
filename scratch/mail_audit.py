# -*- coding: utf-8 -*-
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import DB, init_pool

def run_audit():
    init_pool()
    
    with DB() as (conn, cur):
        # 1. Assessment Alerts
        cur.execute("""
            SELECT registration_number, subject_name, assessment_name, marks_obtained, max_marks 
            FROM student_marks 
            WHERE performance_status = 'Low'
            ORDER BY created_at DESC
        """)
        low_marks = cur.fetchall()
        
        # 2. Attendance Alerts
        cur.execute("""
            SELECT registration_number, subject_name, attendance_date, status 
            FROM attendance 
            WHERE status = 'Absent' 
            ORDER BY attendance_date DESC
        """)
        absences = cur.fetchall()
        
    print("--- MAILING QUEUE AUDIT ---")
    print(f"Low Performance Records: {len(low_marks)}")
    for r in low_marks:
        print(f"  [MARK] ID: {r['registration_number']} | Sub: {r['subject_name']} | Mark: {r['marks_obtained']}/{r['max_marks']}")
        
    print(f"\nAbsence Records: {len(absences)}")
    for r in absences:
        print(f"  [ATTN] ID: {r['registration_number']} | Sub: {r['subject_name']} | Date: {r['attendance_date']}")

if __name__ == "__main__":
    run_audit()
