from database.db import DB, init_pool

def recover():
    init_pool()
    with DB() as (conn, cur):
        sql = """
        INSERT IGNORE INTO students (registration_number, email, password, name, performance) 
        VALUES ('231FA04029', 'student_231fa04029@example.com', 'pass_4029', 'Unknown', 'Low')
        """
        cur.execute(sql)
        conn.commit()
        print("Recovered student 231FA04029")

if __name__ == "__main__":
    recover()
