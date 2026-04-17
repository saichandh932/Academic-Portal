from database.db import DB, init_pool

def check_db():
    init_pool()
    with DB() as (conn, cur):
        sql = """
            INSERT INTO student_marks 
                (registration_number, subject_name, assessment_name, marks_obtained, max_marks, performance_status)
            VALUES 
                (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                marks_obtained = VALUES(marks_obtained),
                max_marks = VALUES(max_marks),
                performance_status = VALUES(performance_status)
        """
        cur.execute(sql, ("231FA04029", "SE", "TEST1", 5, 10, "Low"))
        print("First insert dict:", cur.rowcount)
        conn.commit()

        cur.execute(sql, ("231FA04029", "SE", "TEST1", 9, 10, "Good"))
        print("Second update dict:", cur.rowcount)
        conn.commit()

        cur.execute("SELECT marks_obtained FROM student_marks WHERE registration_number='231FA04029' AND subject_name='SE' AND assessment_name='TEST1'")
        print("Final value:", cur.fetchone())

if __name__ == "__main__":
    check_db()
