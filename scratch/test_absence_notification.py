import urllib.request
import json
import sys

BASE = "http://127.0.0.1:5000"

def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def test_absence_alert():
    print("=== Testing Absence Alert Trigger ===")
    
    # Use a dummy date to avoid collisions if possible, or just a new date
    test_date = "2026-10-10" 
    payload = {
        "subject_name": "ML",
        "date": test_date,
        "records": [
            {"registration_number": "231FA04029", "status": "Absent"},
            {"registration_number": "231FA04033", "status": "Present"}
        ]
    }
    
    print(f"Post attendance for {test_date} with 1 Absentee...")
    try:
        res = post("/api/db/attendance/upload", payload)
        print(f"Response: {res}")
        if res.get("success") and res.get("alerts_sent", 0) > 0:
            print("SUCCESS: Alert dispatch detected in response.")
        else:
            print("FAILED: No alerts dispatched or request failed.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_absence_alert()
