import mysql.connector

def find_missing_data():
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',
        'database': 'student_performance_db'
    }
    try:
        conn = mysql.connector.connect(**config)
        cur = conn.cursor(dictionary=True)
        print("[OK] Connected to MySQL")

        tables = ['student_marks', 'attendance']
        threshold = '231FA04466'

        for table in tables:
            print(f"\n--- Scanning {table} ---")
            cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            total = cur.fetchone()['cnt']
            print(f"  Total records: {total}")

            cur.execute(f"SELECT COUNT(*) as cnt FROM {table} WHERE registration_number > %s", (threshold,))
            missing_count = cur.fetchone()['cnt']
            print(f"  Records AFTER {threshold}: {missing_count}")

            if missing_count > 0:
                cur.execute(f"SELECT * FROM {table} WHERE registration_number > %s LIMIT 5", (threshold,))
                samples = cur.fetchall()
                print("  Sample missing records:")
                for s in samples:
                    print(f"    {s}")

        conn.close()
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    find_missing_data()
