import urllib.request, json, sys, time

BASE = "http://127.0.0.1:5000"

def post(path, body):
    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.getcode()
    except urllib.error.HTTPError as e:
        # Return the error response body if available
        try:
            return json.loads(e.read()), e.code
        except:
            return {"success": False, "error": str(e)}, e.code

def get(path):
    with urllib.request.urlopen(BASE + path) as r:
        return json.loads(r.read()), r.getcode()

PASS = FAIL = 0
def check(label, res):
    global PASS, FAIL
    if isinstance(res, bool):
        ok = res
        detail = ""
    else:
        ok = res.get("success", False)
        detail = res.get("error", "")
    
    PASS += ok; FAIL += (not ok); mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}" + (f"  (Error: {detail})" if not ok and detail else ""))

print("\n=== ACADEMIC ENGINE: INTEGRATION SUITE ===\n")

try:
    # 1. TEST: STUDENT REGISTRATION IDENTIFICATION
    TEST_STUDENT = "231FA04029" 
    
    # 2. TEST: THE LIVE MARKS ENGINE (Sync Test)
    print("[TEST 1] Live Performance Sync...")
    marks_payload = {
        "subject_name": "ML",
        "assessment_name": "Integrated Test-1",
        "max_marks": 100,
        "grades": [{"registration_number": TEST_STUDENT, "marks_obtained": 95}]
    }
    res, code = post("/api/db/marks/upload", marks_payload)
    check("Upload 95% Marks -> Success", res)
    
    # Check if student rank updated to HIGH
    st, code = get(f"/api/db/students/reg/{TEST_STUDENT}")
    check("Student Rank Updated to 'High'", {"success": st.get("student",{}).get("performance") == "High", "error": f"Rank was {st.get('student',{}).get('performance')}"})
    check("Internal Marks Updated to 95.0", {"success": float(st.get("student",{}).get("internal_marks", 0)) == 95.0, "error": f"Score was {st.get('student',{}).get('internal_marks')}"})

    # 3. TEST: THE GLOBAL SHIELD (Slot Locking)
    print("\n[TEST 2] Institutional Global Locking...")
    today = time.strftime("%Y-%m-%d")
    attn_payload = {
        "subject": "ML",
        "date": today,
        "period": 7,
        "records": [{"registration_number": TEST_STUDENT, "status": "Present"}]
    }
    # First submission
    res, _ = post("/api/db/attendance/upload", attn_payload)
    check("Submit P7 Attendance -> Lock Triggered", res)

    # Attempt to post duplicate for SAME SLOT (Different subject "PADCOM")
    # This should be REJECTED by the global lock (403)
    hack_payload = {
        "subject": "PADCOM",
        "date": today,
        "period": 7,
        "records": [{"registration_number": TEST_STUDENT, "status": "Present"}]
    }
    res, code = post("/api/db/attendance/upload", hack_payload)
    check("Duplicate Slot Post rejected (403/Forbidden)", {"success": code == 403, "error": f"Code was {code} - {res.get('error')}"})

    # 4. TEST: ABSENCE ALERT DISPATCH
    print("\n[TEST 3] Absence Alert Dispatching...")
    # Using P8 for a different slot
    alert_payload = {
        "subject": "SE",
        "date": today,
        "period": 8,
        "records": [{"registration_number": TEST_STUDENT, "status": "Absent"}]
    }
    res, code = post("/api/db/attendance/upload", alert_payload)
    if code == 200 or code == 201:
        count = res.get("emails_dispatched", 0)
        check("Post Absence -> Alert triggered", {"success": count > 0, "error": f"Emails dispatched: {count}"})
    else:
        check("Post Absence -> Success", res)

    print(f"\n=== INTEGRATION RESULTS: {PASS} passed / {FAIL} failed ===\n")
    sys.exit(0 if FAIL == 0 else 1)

except Exception as e:
    print(f"\n[FATAL ERROR] Test Suite Aborted: {e}")
    sys.exit(1)
