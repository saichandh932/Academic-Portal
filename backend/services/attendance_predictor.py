# -*- coding: utf-8 -*-
"""
backend/services/attendance_predictor.py
-----------------------------------------
Predicts whether a student will fall below the 75% attendance threshold
before the end of the semester, based on their current trajectory.

Logic
-----
  current_pct   = present / total_conducted
  remaining     = SEMESTER_TOTAL - total_conducted
  If student keeps current rate:
    projected   = (present + remaining * current_rate) / SEMESTER_TOTAL * 100
  "Safe" sessions = min sessions remaining the student must attend to stay >= 75%
  "Max bunks"    = remaining - safe_sessions  (how many more they can miss safely)
"""
from __future__ import annotations

# Estimated total classes per subject in one semester at Vignan (approx)
SEMESTER_TOTAL_CLASSES = 90

DANGER_THRESHOLD = 75.0    # institutional minimum
WARNING_THRESHOLD = 80.0   # buffer zone — start worrying here


def predict_attendance(
    present: int,
    total_conducted: int,
    semester_total: int = SEMESTER_TOTAL_CLASSES,
) -> dict:
    """
    Parameters
    ----------
    present          : classes attended so far
    total_conducted  : total classes held so far
    semester_total   : estimated total classes for the whole semester

    Returns
    -------
    dict with keys:
        current_pct, projected_pct, remaining_classes,
        safe_sessions_needed, max_bunks_left,
        will_drop_below_75, status, status_color, message
    """
    if total_conducted <= 0:
        return _empty_result()

    current_pct = (present / total_conducted) * 100
    remaining   = max(0, semester_total - total_conducted)

    # Project forward at current attendance rate
    projected_present = present + remaining * (present / total_conducted)
    projected_pct     = (projected_present / semester_total) * 100
    projected_pct     = round(min(100.0, projected_pct), 1)

    # Minimum sessions to attend out of remaining to stay >= 75%
    required_total_present = DANGER_THRESHOLD / 100.0 * semester_total
    safe_sessions_needed   = max(0, int(required_total_present - present))
    safe_sessions_needed   = min(safe_sessions_needed, remaining)
    max_bunks_left         = max(0, remaining - safe_sessions_needed)

    will_drop = projected_pct < DANGER_THRESHOLD

    if projected_pct >= WARNING_THRESHOLD:
        status       = "safe"
        status_color = "#22c55e"
        message      = f"You are projected to finish at {projected_pct}%. Attendance is healthy."
    elif projected_pct >= DANGER_THRESHOLD:
        status       = "warning"
        status_color = "#f59e0b"
        message      = (
            f"Projected {projected_pct}% — borderline safe. "
            f"You can afford at most {max_bunks_left} more absences."
        )
    else:
        deficit = round(DANGER_THRESHOLD - projected_pct, 1)
        status  = "critical"
        status_color = "#ef4444"
        message = (
            f"⚠️ Projected {projected_pct}% — {deficit}% below minimum. "
            f"You must attend {safe_sessions_needed} of the remaining {remaining} classes."
        )

    return {
        "current_pct":          round(current_pct, 1),
        "projected_pct":        projected_pct,
        "remaining_classes":    remaining,
        "safe_sessions_needed": safe_sessions_needed,
        "max_bunks_left":       max_bunks_left,
        "will_drop_below_75":   will_drop,
        "status":               status,
        "status_color":         status_color,
        "message":              message,
        "present":              present,
        "total_conducted":      total_conducted,
        "semester_total":       semester_total,
    }


def predict_attendance_for_student(registration_number: str) -> dict:
    """
    Fetches live attendance data from MongoDB for all subjects and runs
    the predictor on each, returning an overall summary + per-subject breakdown.
    """
    from database.db import get_db
    db = get_db()

    records = list(db["attendance"].find(
        {"registration_number": registration_number},
        {"_id": 0}
    ))

    if not records:
        return {"success": False, "error": "No attendance records found."}

    # Aggregate by subject
    from collections import defaultdict
    subject_map: dict[str, dict] = defaultdict(lambda: {"present": 0, "total": 0})
    for r in records:
        subj = r.get("subject_name", "Unknown")
        subject_map[subj]["present"] += 1 if r.get("status", "").lower() == "present" else 0
        subject_map[subj]["total"]   += 1

    subjects_out = []
    any_critical = False
    any_warning  = False

    for subj, counts in subject_map.items():
        pred = predict_attendance(counts["present"], counts["total"])
        pred["subject_name"] = subj
        subjects_out.append(pred)
        if pred["status"] == "critical": any_critical = True
        if pred["status"] == "warning":  any_warning  = True

    # Overall aggregate
    total_present   = sum(v["present"] for v in subject_map.values())
    total_conducted = sum(v["total"]   for v in subject_map.values())
    overall = predict_attendance(total_present, total_conducted,
                                  semester_total=SEMESTER_TOTAL_CLASSES * len(subject_map))

    # Sort worst-first
    STATUS_ORDER = {"critical": 0, "warning": 1, "safe": 2}
    subjects_out.sort(key=lambda x: STATUS_ORDER.get(x["status"], 9))

    overall_status = "critical" if any_critical else ("warning" if any_warning else "safe")

    return {
        "success":        True,
        "overall_status": overall_status,
        "overall":        overall,
        "subjects":       subjects_out,
    }


def _empty_result() -> dict:
    return {
        "current_pct": 0, "projected_pct": 0, "remaining_classes": SEMESTER_TOTAL_CLASSES,
        "safe_sessions_needed": 0, "max_bunks_left": 0, "will_drop_below_75": False,
        "status": "unknown", "status_color": "#94a3b8", "message": "No data yet.",
        "present": 0, "total_conducted": 0, "semester_total": SEMESTER_TOTAL_CLASSES,
    }
