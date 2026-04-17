import sys
import os

# Add the project root to sys.path to import from database and backend
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()
from database.db import DB, init_pool
from backend.config import Config

def migrate():
    # Initialize the pool manually since we're not running the full Flask app
    init_pool()
    
    sql = """
    CREATE TABLE IF NOT EXISTS locked_attendance (
        id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
        subject_name    VARCHAR(50) NOT NULL,
        attendance_date DATE NOT NULL,
        locked_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        UNIQUE KEY (subject_name, attendance_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Immutable registry for finalized attendance dates';
    """
    
    print("[Migration] Creating locked_attendance table...")
    try:
        with DB() as (conn, cur):
            cur.execute(sql)
            conn.commit()
            print("[Migration] Success! Table 'locked_attendance' is now active.")
    except Exception as e:
        print(f"[Migration] Error: {e}")

if __name__ == "__main__":
    migrate()
