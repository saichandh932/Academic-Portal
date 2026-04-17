from database.db import DB, init_pool

def cleanup():
    init_pool()
    with DB() as (conn, cur):
        cur.execute("DELETE FROM students WHERE registration_number LIKE 'SMOKE_TEST_%'")
        deleted = cur.rowcount
        cur.execute("DELETE FROM students WHERE registration_number = '231FA04029'")
        print(f"Deleted smoke test students. Count: {deleted}")
        conn.commit()

if __name__ == "__main__":
    cleanup()
