import urllib.request
import json
from datetime import datetime

BASE = "http://127.0.0.1:5000"

def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.getcode(), json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return 500, str(e)

def test_constraints():
    print("=== Testing Multi-Period Constraints & 8-Hour Rule ===")
    
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = "2026-04-14" # Hardcoded for safety relative to system logs
    
    # CASE 1: Expired Period (Yesterday Period 1)
    print("\n[Case 1] Submitting for Yesterday Period 1 (Should Fail)...")
    payload_expired = {
        "subject_name": "ML",
        "date": yesterday,
        "period": 1,
        "records": [{"registration_number": "231FA04029", "status": "Present"}]
    }
    code, res = post("/api/db/attendance/upload", payload_expired)
    print(f"Status: {code} | Response: {res}")
    
    # CASE 2: Valid Period (Today Period 8)
    # Today's P8 starts at 15:30. Current time is approx 19:10. 
    # Gap is 4 hours. Should succeed.
    print(f"\n[Case 2] Submitting for Today ({today}) Period 8 (Should Succeed)...")
    payload_valid = {
        "subject_name": "ML",
        "date": today,
        "period": 8,
        "records": [{"registration_number": "231FA04029", "status": "Present"}]
    }
    code, res = post("/api/db/attendance/upload", payload_valid)
    print(f"Status: {code} | Response: {res}")

if __name__ == "__main__":
    test_constraints()
