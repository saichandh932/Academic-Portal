from database.db import DB, init_pool

def update_email():
    init_pool()
    with DB() as (conn, cur):
        sql = "UPDATE students SET email = 'inavoluvathsav@gmail.com' WHERE LOWER(registration_number) = LOWER('231fa04528')"
        cur.execute(sql)
        conn.commit()
        print(f"Updated {cur.rowcount} row(s).")

if __name__ == "__main__":
    update_email()
