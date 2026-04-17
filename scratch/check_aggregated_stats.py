from pymongo import MongoClient

def check_aggregate_data():
    MONGO_URI = "mongodb+srv://chandu:Chandu%40420@vignan-academic-cluster.xxqaniq.mongodb.net/?appName=vignan-academic-cluster"
    client = MongoClient(MONGO_URI)
    db = client['student_performance_db']

    print("--- 70 Students: Aggregated Stats Check ---")
    print(f"{'#':<3} | {'Reg Number':<12} | {'Att %':<8} | {'GPA':<5}")
    print("-" * 50)
    
    students = list(db['students'].find({}, {'registration_number': 1, 'attendance': 1, 'internal_marks': 1, '_id': 0}).sort('registration_number', 1))
    
    for i, s in enumerate(students):
        reg = s['registration_number']
        att = s.get('attendance', 'MISSING')
        gpa = s.get('internal_marks', 'MISSING')
        print(f"{i+1:<3} | {reg:<12} | {att:<8} | {gpa:<5}")
        
    client.close()

if __name__ == "__main__":
    check_aggregate_data()
