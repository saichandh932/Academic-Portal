from pymongo import MongoClient
import json

def generate_report():
    MONGO_URI = "mongodb+srv://chandu:Chandu%40420@vignan-academic-cluster.xxqaniq.mongodb.net/?appName=vignan-academic-cluster"
    client = MongoClient(MONGO_URI)
    db = client['student_performance_db']

    print("=" * 80)
    print(f"{'#':<3} | {'Reg Number':<12} | {'Name':<30} | {'Marks':<5} | {'Att':<3}")
    print("-" * 80)

    students = list(db['students'].find({}, {'registration_number': 1, 'name': 1, '_id': 0}).sort('registration_number', 1))

    for i, s in enumerate(students):
        reg = s['registration_number']
        name = s.get('name', 'N/A')
        
        m_count = db['student_marks'].count_documents({'registration_number': reg})
        a_count = db['attendance'].count_documents({'registration_number': reg})
        
        print(f"{i+1:<3} | {reg:<12} | {name[:30]:<30} | {m_count:<5} | {a_count:<3}")
        
    print("=" * 80)

    print("\n--- Admin Login Check ---")
    admins = list(db['admins'].find({}, {'_id': 0, 'password': 0}))
    print(f"Total Admin Accounts: {len(admins)}")
    for a in admins:
        print(f"  - {a.get('username'):<15} : {a.get('assigned_subject')}")

    client.close()

if __name__ == "__main__":
    generate_report()
