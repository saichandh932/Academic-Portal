# -*- coding: utf-8 -*-
"""
backend/services/feature_extractor.py
---------------------------------------
Derives LIVE ML features for a student from real MongoDB data.

Instead of relying on the static CSV values stored at student-creation time,
this module computes each feature from the actual attendance and marks records
that teachers have entered — making the ML model truly data-driven.

Features derived:
  - attendance      → % present across all subjects from the attendance collection
  - internal_marks  → average percentage across all ISE/CIE/quiz marks
  - assignments     → average assignment percentage
  - previous_score  → falls back to the stored value (no live source yet)
  - study_hours     → falls back to the stored value (self-reported)
"""
from __future__ import annotations
from database.db import get_db


# Keywords that identify assignment-type assessments
_ASSIGNMENT_KEYWORDS = ["assignment", "assign", "homework", "hw", "lab"]
# Keywords that identify internal exam assessments
_INTERNAL_KEYWORDS   = ["ise", "cie", "mid", "internal", "quiz", "test", "unit"]


def _is_assignment(assessment_name: str) -> bool:
    name = assessment_name.lower()
    return any(kw in name for kw in _ASSIGNMENT_KEYWORDS)


def _is_internal(assessment_name: str) -> bool:
    name = assessment_name.lower()
    return any(kw in name for kw in _INTERNAL_KEYWORDS)


def extract_features(registration_number: str) -> dict:
    """
    Derives all 5 ML features from live MongoDB data for a given student.

    Returns a dict with keys:
        study_hours, attendance, previous_score, assignments, internal_marks
    Falls back to stored student record values when live data is unavailable.
    """
    db = get_db()

    # ── 1. Load base student record (for fallbacks) ───────────────────────────
    student = db["students"].find_one(
        {"registration_number": registration_number},
        {"_id": 0, "study_hours": 1, "attendance": 1,
         "previous_score": 1, "assignments": 1, "internal_marks": 1}
    ) or {}

    fallback_study_hours    = float(student.get("study_hours",    4.0) or 4.0)
    fallback_attendance     = float(student.get("attendance",    75.0) or 75.0)
    fallback_prev_score     = float(student.get("previous_score",50.0) or 50.0)
    fallback_assignments    = float(student.get("assignments",   50.0) or 50.0)
    fallback_internal_marks = float(student.get("internal_marks",50.0) or 50.0)

    # ── 2. LIVE attendance from attendance collection ─────────────────────────
    att_pipeline = [
        {"$match": {"registration_number": registration_number}},
        {"$group": {
            "_id": None,
            "total":   {"$sum": 1},
            "present": {"$sum": {"$cond": [{"$eq": ["$status", "Present"]}, 1, 0]}}
        }}
    ]
    att_result = list(db["attendance"].aggregate(att_pipeline))
    if att_result and att_result[0]["total"] > 0:
        r = att_result[0]
        live_attendance = round((r["present"] / r["total"]) * 100, 2)
    else:
        live_attendance = fallback_attendance

    # ── 3. LIVE marks — split into internal exams vs assignments ──────────────
    marks_cursor = list(db["student_marks"].find(
        {"registration_number": registration_number},
        {"_id": 0, "assessment_name": 1, "marks_obtained": 1, "max_marks": 1}
    ))

    internal_pcts  = []
    assignment_pcts = []

    for m in marks_cursor:
        max_m = float(m.get("max_marks", 0) or 0)
        if max_m == 0:
            continue
        pct = (float(m.get("marks_obtained", 0) or 0) / max_m) * 100
        aname = m.get("assessment_name", "")
        if _is_assignment(aname):
            assignment_pcts.append(pct)
        else:
            # treat everything else (ISE, quiz, unit test …) as internal
            internal_pcts.append(pct)

    live_internal_marks = (
        round(sum(internal_pcts) / len(internal_pcts), 2)
        if internal_pcts else fallback_internal_marks
    )
    live_assignments = (
        round(sum(assignment_pcts) / len(assignment_pcts), 2)
        if assignment_pcts else fallback_assignments
    )

    # ── 4. Assemble feature dict ───────────────────────────────────────────────
    features = {
        "study_hours":    fallback_study_hours,      # self-reported; no live source
        "attendance":     live_attendance,
        "previous_score": fallback_prev_score,        # from previous semester; static
        "assignments":    live_assignments,
        "internal_marks": live_internal_marks,
    }

    # Metadata for transparency
    meta = {
        "total_attendance_records": att_result[0]["total"] if att_result else 0,
        "total_marks_records":      len(marks_cursor),
        "internal_exam_count":      len(internal_pcts),
        "assignment_count":         len(assignment_pcts),
        "live_attendance_used":     att_result[0]["total"] > 0 if att_result else False,
        "live_marks_used":          len(marks_cursor) > 0,
    }

    return features, meta
