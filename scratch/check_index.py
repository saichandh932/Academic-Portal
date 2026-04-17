from database.db import DB, init_pool

def check_db():
    init_pool()
    with DB() as (conn, cur):
        cur.execute("SHOW INDEX FROM student_marks")
        indices = cur.fetchall()
        for idx in indices:
            print(f"Key: {idx['Key_name']}, Col: {idx['Column_name']}, Non_Unique: {idx['Non_unique']}")
            
        cur.execute("SELECT registration_number, subject_name, assessment_name, COUNT(*) as cnt FROM student_marks GROUP BY registration_number, subject_name, assessment_name HAVING cnt > 1")
        dups = cur.fetchall()
        print(f"Duplicates found: {len(dups)}")
        for d in dups:
            print(d)

if __name__ == "__main__":
    check_db()
