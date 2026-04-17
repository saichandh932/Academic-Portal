import requests
import time

def test_api():
    url = "http://127.0.0.1:5000/api/db/marks/upload"
    
    # 1. Update 1
    payload1 = {
        "subject_name": "SE",
        "assessment_name": "TEST API",
        "max_marks": 20,
        "grades": [
            {"registration_number": "231FA04029", "marks_obtained": 10}
        ]
    }
    r = requests.post(url, json=payload1)
    print("Update 1:", r.json())
    
    # 2. Get
    r = requests.get("http://127.0.0.1:5000/api/db/marks")
    marks = [m for m in r.json().get('marks', []) if m['assessment_name'] == 'TEST API']
    print("Fetch 1:", marks)

    time.sleep(1)

    # 3. Update 2
    payload2 = {
        "subject_name": "SE",
        "assessment_name": "TEST API",
        "max_marks": 20,
        "grades": [
            {"registration_number": "231FA04029", "marks_obtained": 15}
        ]
    }
    r = requests.post(url, json=payload2)
    print("Update 2:", r.json())
    
    # 4. Get
    r = requests.get("http://127.0.0.1:5000/api/db/marks")
    marks = [m for m in r.json().get('marks', []) if m['assessment_name'] == 'TEST API']
    print("Fetch 2:", marks)

if __name__ == "__main__":
    test_api()
