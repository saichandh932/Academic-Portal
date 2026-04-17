import urllib.request, urllib.error, json, sys

BASE = "http://127.0.0.1:5000"

def get(path):
    with urllib.request.urlopen(BASE + path) as r:
        return json.loads(r.read())

def post(path, body=None):
    data = json.dumps(body or {}).encode()
    req  = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

PASS = FAIL = 0

def check(label, cond, detail=""):
    global PASS, FAIL
    ok = bool(cond)
    PASS += ok; FAIL += not ok
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  ({detail})" if detail else ""))

print("\n=== Phase 5 Alert & Dashboard Smoke Tests ===\n")

# ── Dashboard ─────────────────────────────────────────────────────────────────
d, _ = post("/api/predict", {
    "study_hours": 1.0, "attendance": 25.0,
    "previous_score": 18.0, "assignments": 8.0, "internal_marks": 6.0
})
check("POST /api/predict low risk student", d["success"])

import time; time.sleep(0.4)

dash = get("/api/dashboard")
check("GET /api/dashboard success",               dash["success"])
check("GET /api/dashboard prediction_stats",       "prediction_stats" in dash)
check("GET /api/dashboard student_stats",          "student_stats" in dash)
check("GET /api/dashboard alert_stats",            "alert_stats" in dash)
check("GET /api/dashboard alerts_by_type dict",    isinstance(dash.get("alerts_by_type"), dict))
check("GET /api/dashboard recent_critical_alerts", isinstance(dash.get("recent_critical_alerts"), list))
check("GET /api/dashboard recent_predictions",     isinstance(dash.get("recent_predictions"), list))
check("GET /api/dashboard prediction_trend",       isinstance(dash.get("prediction_trend"), list))
check("GET /api/dashboard at_risk_students",       isinstance(dash.get("at_risk_students"), list))
print(f"     prediction_stats={dash['prediction_stats']}")
print(f"     alert_stats={dash['alert_stats']}")

# ── Batch scan ────────────────────────────────────────────────────────────────
scan, sc = post("/api/dashboard/scan", {"run_by": "smoke_test"})
check("POST /api/dashboard/scan success",          scan["success"], f"HTTP {sc}")
check("POST /api/dashboard/scan has students_total", "students_total" in scan)
check("POST /api/dashboard/scan students_total>0", scan.get("students_total", 0) > 0)
print(f"     scan result={dict(list(scan.items())[1:])}")

# ── At-risk students ──────────────────────────────────────────────────────────
ar = get("/api/dashboard/at-risk?limit=5")
check("GET /api/dashboard/at-risk success",        ar["success"])
check("GET /api/dashboard/at-risk is list",        isinstance(ar.get("students"), list))
print(f"     at-risk count={ar['count']}")
if ar["count"] > 0:
    print(f"     first={ar['students'][0]}")

# ── Notifications config ──────────────────────────────────────────────────────
nc = get("/api/notifications/config")
check("GET /api/notifications/config success",     nc["success"])
check("GET /api/notifications/config thresholds",  "thresholds" in nc)
check("GET /api/notifications/config no password", nc.get("smtp_password") in ("***", "(not set)"))
print(f"     email_enabled={nc['email_enabled']} smtp_host={nc['smtp_host']}")

# ── Test email (email disabled — should return 200 with message) ─────────────
te, tc = post("/api/notifications/test", {"recipient": "test@example.com"})
check("POST /api/notifications/test responds",     tc in (200, 502))
print(f"     test email: success={te.get('success')} msg={te.get('message')}")

# ── Manual alert email ────────────────────────────────────────────────────────
alerts_list = get("/api/alerts?limit=1")
if alerts_list["count"] > 0:
    aid = alerts_list["alerts"][0]["id"]
    ma, mc = post("/api/notifications/send-alert", {"alert_id": aid})
    check("POST /api/notifications/send-alert responds", mc == 200)
    print(f"     manual alert email: {ma.get('message')}")
else:
    print("  [SKIP] No alerts to manually send")
    PASS += 1

# ── Alert system end-to-end: predict low -> check new alerts ─────────────────
before = get("/api/alerts/summary")
open_before = before.get("open", 0)

# Another low-performing prediction
lp, _ = post("/api/predict", {
    "study_hours": 0.5, "attendance": 20.0,
    "previous_score": 10.0, "assignments": 5.0, "internal_marks": 3.0
})
check("POST /api/predict ultra-low success", lp["success"])
check("POST /api/predict ultra-low is Low",  lp["prediction"] == "Low",
      f"got {lp['prediction']}")

time.sleep(0.4)

after = get("/api/alerts/summary")
open_after = after.get("open", 0)
check("Alerts increased after low prediction",
      open_after >= open_before,
      f"before={open_before} after={open_after}")
print(f"     alerts before={open_before} after={open_after} delta={open_after - open_before}")

# ── Alert by type filter ──────────────────────────────────────────────────────
lp_alerts = get("/api/alerts?resolved=false&severity=critical&limit=5")
check("GET /api/alerts critical filter works",     lp_alerts["success"])
if lp_alerts["alerts"]:
    check("All returned alerts are critical",
          all(a["severity"] == "critical" for a in lp_alerts["alerts"]))

print(f"\n=== Results: {PASS} passed / {FAIL} failed ===\n")
sys.exit(0 if FAIL == 0 else 1)
