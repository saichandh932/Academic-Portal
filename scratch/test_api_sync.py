import requests
import json
from datetime import datetime

def test_sync():
    base_url = "http://127.0.0.1:5000/api/db/attendance"
    today = datetime.now().strftime("%Y-%m-%d")
    period = 6
    
    print(f"--- TESTING SYNC FOR {today} P{period} ---")
    
    # 1. Fetch locks
    print("\n[1] Fetching Locks...")
    res_locks = requests.get(f"{base_url}/locks?subject=PADCOM")
    print(f"Status: {res_locks.status_code}")
    print(f"Body: {json.dumps(res_locks.json(), indent=2)}")
    
    # 2. Fetch Attendance for PADCOM
    print("\n[2] Fetching PADCOM Attendance (Should pull ML's data)...")
    res_att = requests.get(f"{base_url}/?subject=PADCOM&date={today}&period={period}")
    print(f"Status: {res_att.status_code}")
    data = res_att.json()
    records = data.get('records', [])
    print(f"Returned {len(records)} records.")
    
    absentees = [r for r in records if r['status'] == 'Absent']
    print(f"Found {len(absentees)} absentees.")
    for a in absentees:
        print(f"  ID: {a['registration_number']} | Marked by: {a.get('_locked_by', 'Unknown')}")

if __name__ == "__main__":
    try:
        test_sync()
    except Exception as e:
        print(f"Error connecting to server: {e}")
