import mysql.connector
from pymongo import MongoClient
import sys

def master_audit():
    MYSQL_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',
        'database': 'student_performance_db'
    }
    MONGO_URI = "mongodb+srv://chandu:Chandu%40420@vignan-academic-cluster.xxqaniq.mongodb.net/?appName=vignan-academic-cluster"
    
    print("=" * 60)
    print("  MYSQL vs MONGODB ATLAS - MASTER DATA AUDIT")
    print("=" * 60)
    
    try:
        mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
        mysql_cur = mysql_conn.cursor(dictionary=True)
        print("[OK] Connected to Local MySQL")
    except Exception as e:
        print(f"[ERROR] MySQL connection failed. Is MySQL running? {e}")
        return

    try:
        mongo_client = MongoClient(MONGO_URI)
        mongo_db = mongo_client['student_performance_db']
        print("[OK] Connected to MongoDB Atlas")
    except Exception as e:
        print(f"[ERROR] MongoDB connection failed: {e}")
        return

    tables = ["students", "admins", "student_marks", "attendance", "locked_assessments", "locked_attendance", "prediction_logs", "alert_records"]
    
    print(f"\n{'Table Name':<20} | {'MySQL':<8} | {'MongoDB':<8} | {'Status'}")
    print("-" * 60)
    
    for table in tables:
        # MySQL count
        try:
            mysql_cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            m_count = mysql_cur.fetchone()['cnt']
        except:
            m_count = "N/A"
            
        # Mongo count
        try:
            n_count = mongo_db[table].count_documents({})
        except:
            n_count = "N/A"
            
        status = "MATCH" if m_count == n_count else "MISMATCH!"
        if m_count == "N/A": status = "TBL MISSING"
        
        print(f"{table:<20} | {m_count:<8} | {n_count:<8} | {status}")

    print("\n--- Deep Check for Marks ---")
    if "student_marks" in tables:
        mysql_cur.execute("SELECT * FROM student_marks")
        m_marks = mysql_cur.fetchall()
        n_marks = list(mongo_db["student_marks"].find())
        print(f"Total Unique IDs in MySQL: {len(m_marks)}")
        print(f"Total Records in MongoDB: {len(n_marks)}")
        
        if len(m_marks) > len(n_marks):
            # Find a few missing ones
            m_ids = set()
            for row in m_marks:
                # Construct a logical key (reg, sub, assessment)
                key = (row['registration_number'], row['subject_name'], row['assessment_name'])
                m_ids.add(key)
            
            n_ids = set()
            for row in n_marks:
                key = (row['registration_number'], row['subject_name'], row['assessment_name'])
                n_ids.add(key)
            
            missing = m_ids - n_ids
            print(f"Sample MISSING records (first 5):")
            for i, mix in enumerate(list(missing)[:5]):
                print(f"  {mix}")

    mysql_conn.close()
    mongo_client.close()

if __name__ == "__main__":
    master_audit()
