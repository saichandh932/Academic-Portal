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

PASS = 0
FAIL = 0

def check(label, cond):
    global PASS, FAIL
    status = "PASS" if cond else "FAIL"
    if cond:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{status}] {label}")

print("\n=== Smoke Tests ===\n")

# GET /api
r = get("/api")
check("GET /api returns endpoint map", "endpoints" in r)

# GET /api/health
h = get("/api/health")
check("GET /api/health -> success", h.get("success") is True)
check("GET /api/health -> status ok", h.get("status") == "ok")

# POST /api/predict
pred = post("/api/predict", {
    "study_hours": 8.0, "attendance": 85.0,
    "previous_score": 75.0, "assignments": 90.0, "internal_marks": 40.0
})
check("POST /api/predict -> success", pred.get("success") is True)
check("POST /api/predict -> prediction field", "prediction" in pred)
check("POST /api/predict -> confidence float", isinstance(pred.get("confidence"), float))
check("POST /api/predict -> 3 proba classes", len(pred.get("probabilities", {})) == 3)
print(f"     prediction={pred['prediction']}  confidence={pred['confidence']}")

# POST /api/predict validate error
try:
    bad = post("/api/predict", {"study_hours": 8.0})
    check("POST /api/predict bad payload -> success=False", bad.get("success") is False)
except Exception:
    check("POST /api/predict bad payload -> 422 error", True)

# POST /api/predict/batch
batch = post("/api/predict/batch", {"students": [
    {"study_hours":8.0,"attendance":85.0,"previous_score":75.0,"assignments":90.0,"internal_marks":40.0},
    {"study_hours":1.0,"attendance":30.0,"previous_score":20.0,"assignments":10.0,"internal_marks":11.0},
]})
check("POST /api/predict/batch -> success",      batch.get("success") is True)
check("POST /api/predict/batch -> 2 results",    len(batch.get("results", [])) == 2)
check("POST /api/predict/batch -> total=2",      batch.get("total") == 2)
for res in batch["results"]:
    print(f"     i={res['index']} pred={res['prediction']} conf={res['confidence']}")

# GET /api/students
sl = get("/api/students?page=1&per_page=5")
check("GET /api/students -> success",    sl.get("success") is True)
check("GET /api/students -> 5 records",  len(sl.get("students", [])) == 5)
check("GET /api/students -> total>0",    sl.get("total", 0) > 0)

# GET /api/students/1
s1 = get("/api/students/1")
check("GET /api/students/1 -> success",  s1.get("success") is True)
check("GET /api/students/1 -> has id",   s1.get("student", {}).get("id") == 1)

# POST /api/students
new = post("/api/students", {
    "study_hours": 7.5, "attendance": 78.0,
    "previous_score": 65.0, "assignments": 80.0, "internal_marks": 35.0
})
check("POST /api/students -> success",           new.get("success") is True)
check("POST /api/students -> has id",            "id" in new)
check("POST /api/students -> performance set",   "performance" in new.get("student", {}))
print(f"     new student id={new['id']} perf={new['student']['performance']} auto={new['performance_auto']}")

# GET /api/students/stats
st = get("/api/students/stats")
check("GET /api/students/stats -> success",      st.get("success") is True)
check("GET /api/students/stats -> class_counts", "class_counts" in st)
check("GET /api/students/stats -> total>0",      st.get("total", 0) > 0)

# GET /api/students/search
sr = get("/api/students/search?performance=High&min_attendance=70")
check("GET /api/students/search -> success",     sr.get("success") is True)
check("GET /api/students/search -> all High",
      all(x["performance"] == "High" for x in sr.get("students", [])))
print(f"     search count={sr['count']}")

# GET /api/model/info
mi = get("/api/model/info")
check("GET /api/model/info -> success",          mi.get("success") is True)
check("GET /api/model/info -> 3 classes",        len(mi.get("classes", [])) == 3)
check("GET /api/model/info -> 5 features",       mi.get("num_features") == 5)

# GET /api/model/coefficients
co = get("/api/model/coefficients")
check("GET /api/model/coefficients -> success",  co.get("success") is True)
check("GET /api/model/coefficients -> 3 classes", len(co.get("coefficients", {})) == 3)
check("GET /api/model/coefficients -> all feats",
      all(len(v) == 5 for v in co["coefficients"].values()))

print(f"\n=== Results: {PASS} passed / {FAIL} failed ===\n")
sys.exit(0 if FAIL == 0 else 1)
