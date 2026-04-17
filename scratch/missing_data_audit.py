from pymongo import MongoClient

def audit_data():
    MONGO_URI = "mongodb+srv://chandu:Chandu%40420@vignan-academic-cluster.xxqaniq.mongodb.net/?appName=vignan-academic-cluster"
    client = MongoClient(MONGO_URI)
    db = client['student_performance_db']

    print("--- Marks Audit ---")
    marks = list(db['student_marks'].find({}, {'_id': 0}))
    print(f"Total Marks Records: {len(marks)}")
    for m in marks:
        print(f"  {m.get('registration_number')} | {m.get('subject_name')} | {m.get('assessment_name')} | {m.get('marks_obtained')}")

    print("\n--- Attendance Audit (First 5) ---")
    attendance = list(db['attendance'].find({}, {'_id': 0}).limit(5))
    for a in attendance:
        print(f"  {a.get('registration_number')} | {a.get('subject_name')} | {a.get('attendance_date')} | {a.get('status')}")

    print("\n--- Student Sample ---")
    student = db['students'].find_one({"registration_number": "231FA04672"}, {"_id": 0})
    if student:
        print(f"Found 231FA04672: Name={student.get('name')}, GPA={student.get('internal_marks')}")
    else:
        print("Student 231FA04672 NOT FOUND in MongoDB!")

    client.close()

if __name__ == "__main__":
    audit_data()
