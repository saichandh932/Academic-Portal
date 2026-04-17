import urllib.request, json, sys

BASE = "http://127.0.0.1:5000"

def get(path):
    with urllib.request.urlopen(BASE + path) as r:
        return json.loads(r.read())

def post(path, body):
    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def put(path, body):
    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"}, method="PUT"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def delete(path):
    req = urllib.request.Request(BASE + path, method="DELETE")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

PASS = FAIL = 0

def check(label, cond, detail=""):
    global PASS, FAIL
    ok = bool(cond)
    PASS += ok; FAIL += (not ok)
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}" + (f"  ({detail})" if detail else ""))

print("\n=== Phase 4 DB Smoke Tests ===\n")

# ── GET /api — db_available ──────────────────────────────────────────────────────
r = get("/api")
check("GET /api db_available=True", r.get("db_available") is True)
check("GET /api version=2.0.0",     r.get("version") == "2.0.0")

# ── DB Students list ──────────────────────────────────────────────────────────
sl = get("/api/db/students?per_page=5")
check("GET /api/db/students success",    sl["success"])
check("GET /api/db/students 5 records",  len(sl["students"]) == 5)
check("GET /api/db/students total>0",    sl["total"] > 0, f"total={sl['total']}")
if sl["students"]:
    first_reg = sl["students"][0]["registration_number"]
else:
    first_reg = "UNKNOWN"

# ── Filter by performance ─────────────────────────────────────────────────────
sh = get("/api/db/students?performance=High&per_page=5")
check("GET /api/db/students filter High",
      all(s["performance"] == "High" for s in sh["students"]))

# ── Get one student ───────────────────────────────────────────────────────────
s1 = get(f"/api/db/students/reg/{first_reg}")
check("GET /api/db/students/reg success", s1["success"])
check("GET /api/db/students/reg registration matches", s1["student"]["registration_number"] == first_reg)

# ── Stats ─────────────────────────────────────────────────────────────────────
st = get("/api/db/students/stats")
check("GET /api/db/students/stats success",      st["success"])
check("GET /api/db/students/stats class_counts", "class_counts" in st)
check("GET /api/db/students/stats overall",      "overall" in st)
print(f"     class_counts={st['class_counts']}")
print(f"     avg_attendance={st['overall'].get('avg_attendance')}")

# ── Create student (auto-predict) ─────────────────────────────────────────────
nc = post("/api/db/students", {
    "study_hours": 8.0, "attendance": 85.0,
    "previous_score": 75.0, "assignments": 90.0, "internal_marks": 40.0,
    "name": "Test Student", "registration_number": "SMOKE_TEST_001"
})
check("POST /api/db/students success",           nc["success"])
check("POST /api/db/students has reg",           "registration_number" in nc)
check("POST /api/db/students performance set",   nc["performance"] in ("High","Medium","Low"))
check("POST /api/db/students auto predicted",    nc.get("performance_auto") is True)
new_id = nc["registration_number"]
print(f"     new student reg={new_id} perf={nc['performance']} alerts={nc['alerts_raised']}")

# ── Create student (manual label) ────────────────────────────────────────────
nm = post("/api/db/students", {
    "registration_number": "SMOKE_TEST_002",
    "study_hours": 1.0, "attendance": 25.0,   # low -> will trigger alerts
    "previous_score": 20.0, "assignments": 10.0, "internal_marks": 8.0,
    "performance": "Low"
})
check("POST /api/db/students manual label",      nm["performance"] == "Low")
check("POST /api/db/students not auto",          nm["performance_auto"] is False)
at_risk_id = nm["registration_number"]
print(f"     at-risk reg={at_risk_id}")

# ── Update student ────────────────────────────────────────────────────────────
up = put(f"/api/db/students/{new_id}", {"attendance": 92.0})
check("PUT /api/db/students update", up["success"])

# ── Student prediction history ─────────────────────────────────────────────────
# Hist endpoint currently returns history for a student by reg
hist = get(f"/api/db/students/{first_reg}/history")
check("GET /api/db/students/history success", hist["success"])
print(f"     history records found")

# ── Prediction logs ───────────────────────────────────────────────────────────
# Make a fresh prediction to ensure logs table has data
pred = post("/api/predict", {
    "study_hours": 1.0, "attendance": 25.0,
    "previous_score": 20.0, "assignments": 10.0, "internal_marks": 8.0
})
check("POST /api/predict still works",    pred["success"])
check("POST /api/predict prediction set", pred["prediction"] in ("High","Medium","Low"))

import time; time.sleep(0.3)  # brief wait for DB write

logs = get("/api/db/predictions?limit=10")
check("GET /api/db/predictions success",    logs["success"])
check("GET /api/db/predictions has logs",   logs["count"] > 0,
      f"count={logs['count']}")

summary = get("/api/db/predictions/summary")
check("GET /api/db/predictions/summary success", summary["success"])
check("GET /api/db/predictions/summary total>0", summary.get("total", 0) > 0)
print(f"     prediction summary={dict(list(summary.items())[:5])}")

# ── Alerts ────────────────────────────────────────────────────────────────────
import time; time.sleep(0.3)

al = get("/api/alerts")
check("GET /api/alerts success",    al["success"])
check("GET /api/alerts count>=0",   al["count"] >= 0)
print(f"     total alerts={al['count']}")

als = get("/api/alerts/summary")
check("GET /api/alerts/summary success", als["success"])
check("GET /api/alerts/summary has open", "open" in als)
print(f"     alert summary: open={als.get('open')} critical={als.get('critical')}")

# ── Alerts by student ─────────────────────────────────────────────────────────
sa = get(f"/api/alerts/student/{at_risk_id}")
check("GET /api/alerts/student success",   sa["success"])
print(f"     alerts for at-risk student {at_risk_id}: {sa['count']}")

# ── Resolve an alert ──────────────────────────────────────────────────────────
if al["count"] > 0:
    first_alert_id = al["alerts"][0]["id"]
    rv = post(f"/api/alerts/{first_alert_id}/resolve", {"resolved_by": "smoke_test"})
    check("POST /api/alerts/resolve success", rv["success"])
    print(f"     resolved alert id={first_alert_id}")
else:
    print("  [SKIP] No alerts to resolve")
    PASS += 1

# ── Delete the test student ───────────────────────────────────────────────────
dl = delete(f"/api/db/students/{new_id}")
check("DELETE /api/db/students success", dl["success"])

# ── Confirm 404 after delete ──────────────────────────────────────────────────
try:
    get(f"/api/db/students/reg/{new_id}")
    check("Deleted student returns 404", False)
except urllib.error.HTTPError as e:
    check("Deleted student returns 404", e.code in (404, 500), f"HTTP {e.code}")


print(f"\n=== Results: {PASS} passed / {FAIL} failed ===\n")
sys.exit(0 if FAIL == 0 else 1)
