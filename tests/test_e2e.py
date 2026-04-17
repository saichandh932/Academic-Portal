import subprocess
import time
import urllib.request
import urllib.error
import urllib.parse
import json
import os
import sys

# Configurations
BASE_URL = "http://127.0.0.1:5000"
PROC = None

# Custom simple assert/check
PASS = FAIL = 0
def check(label, cond, details=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label} " + (f"({details})" if details else ""))

def start_server():
    global PROC
    print("\n[E2E] Starting integrated Production Server (Waitress)...")
    env = os.environ.copy()
    env["FLASK_DEBUG"] = "false" # Force production mode
    if "DB_PASSWORD" not in env:
        env["DB_PASSWORD"] = "root"  # Default fallback for testing
    
    PROC = subprocess.Popen(
        [sys.executable, "run.py"], 
        env=env,
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT
    )
    
    # Wait for the server to be responsive
    for _ in range(15):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api", timeout=1) as res:
                if res.status == 200:
                    print("[E2E] Server is up and responding!")
                    return True
        except (urllib.error.URLError, ConnectionResetError):
            pass
        time.sleep(1)
        
    print("[E2E] Server failed to start or respond in time.")
    return False

def test_frontend_serving():
    print("\n--- Testing React Frontend Serving ---")
    try:
        req = urllib.request.Request(f"{BASE_URL}/")
        with urllib.request.urlopen(req) as res:
            html = res.read().decode('utf-8')
            code = res.status
            
            check("Root '/' returns HTTP 200", code == 200, f"Got HTTP {code}")
            check("Root '/' returns index.html", "<div id=\"root\"></div>" in html, "React root div not found")
            check("Title is Vignan Academic Portal", "Vignan Academic Portal" in html)
            
    except Exception as e:
        check("Root '/' fetch successful", False, str(e))
        
    try:
        req = urllib.request.Request(f"{BASE_URL}/student/123")
        with urllib.request.urlopen(req) as res:
            html = res.read().decode('utf-8')
            check("SPA Catch-All Route (e.g. /student/123) serves index.html", "<div id=\"root\"></div>" in html)
    except Exception as e:
        check("SPA Catch-All fetch successful", False, str(e))


def test_api_integration():
    print("\n--- Testing API & Machine Learning ---")
    
    # 1. Prediction Flow (Machine Learning Integration)
    try:
        data = json.dumps({
            "study_hours": 10.0, "attendance": 90.0, 
            "previous_score": 85.0, "assignments": 95.0, "internal_marks": 90.0
        }).encode()
        req = urllib.request.Request(f"{BASE_URL}/api/predict", data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req) as res:
            body = json.loads(res.read())
            check("Prediction API works end-to-end", body.get("success") == True)
            check("ML probability generated", "probabilities" in body)
    except Exception as e:
        check("Prediction API works end-to-end", False, str(e))
        
    # 2. Database Integration
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/dashboard")
        with urllib.request.urlopen(req) as res:
            body = json.loads(res.read())
            check("Dashboard Database API works", body.get("success") == True)
            check("Database student statistics returned", "student_stats" in body)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        check("Dashboard Database API works", False, f"HTTP {e.code}: {error_body}")
    except Exception as e:
        check("Dashboard Database API works", False, str(e))

def cleanup():
    if PROC:
        print("\n[E2E] Terminating server...")
        PROC.terminate()
        try:
            PROC.wait(timeout=3)
        except subprocess.TimeoutExpired:
            PROC.kill()
        
        # Read final lines of output
        out = PROC.stdout.read().decode('utf-8', errors='replace')
        if "Traceback" in out or "Error" in out:
            print("[E2E] Server logged some errors/tracebacks:")
            print("\n".join(l for l in out.splitlines() if "Error" in l or "Traceback" in l))

if __name__ == "__main__":
    print("=== Phase 7 Integrated E2E Test Suite ===")
    
    if not start_server():
        cleanup()
        sys.exit(1)
        
    try:
        test_frontend_serving()
        test_api_integration()
    finally:
        cleanup()
        
    print(f"\n=== Results: {PASS} passed / {FAIL} failed ===")
    if FAIL > 0:
        sys.exit(1)
    else:
        print("Integration & E2E Validation PASSED. Deployment Ready.")
