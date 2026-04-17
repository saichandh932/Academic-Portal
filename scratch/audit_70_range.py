from pymongo import MongoClient

def audit_70():
    MONGO_URI = "mongodb+srv://chandu:Chandu%40420@vignan-academic-cluster.xxqaniq.mongodb.net/?appName=vignan-academic-cluster"
    client = MongoClient(MONGO_URI)
    db = client['student_performance_db']

    print("--- 70 Students in MongoDB (Sorted) ---")
    students = list(db['students'].find({}, {'registration_number': 1, 'name': 1, '_id': 0}).sort('registration_number', 1))
    for i, s in enumerate(students):
        print(f"{i+1:2}. {s['registration_number']} | {s.get('name')}")
        if s['registration_number'] == "231FA04466":
            print(">>> THRESHOLD REACHED: 231FA04466 <<<")

    print(f"\nTotal: {len(students)}")
    client.close()

if __name__ == "__main__":
    audit_70()
