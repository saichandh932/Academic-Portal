# -*- coding: utf-8 -*-
"""
backend/services/alert_engine.py
----------------------------------
Dashboard analytics using MongoDB aggregations.
"""
from __future__ import annotations
from datetime import datetime
from database.db import get_db


def get_dashboard_data() -> dict:
    db = get_db()

    # 1. Registration Stats
    total_students = db["students"].count_documents({})

    # 2. Gradebook Entry Stats
    total_marks_count = db["student_marks"].count_documents({})

    # 3. Performance Breakdown
    pipeline = [
        {"$group": {
            "_id": "$performance_status",
            "count": {"$sum": 1}
        }}
    ]
    perf = {r["_id"]: r["count"] for r in db["student_marks"].aggregate(pipeline)}
    low_count = perf.get("Low", 0)
    good_count = perf.get("Good", 0)

    # 4. Recent "Below Threshold" flags
    recent_critical = list(db["student_marks"].find(
        {"performance_status": "Low"},
        {"_id": 0, "registration_number": 1, "subject_name": 1,
         "assessment_name": 1, "marks_obtained": 1, "max_marks": 1, "created_at": 1}
    ).sort("created_at", -1).limit(10))

    def _clean(d: dict) -> dict:
        if not d: return {}
        out = {}
        for k, v in d.items():
            if v is None:
                out[k] = 0
            elif hasattr(v, "isoformat"):
                out[k] = str(v)
            else:
                out[k] = v
        return out

    return {
        "generated_at": datetime.now().isoformat(),
        "student_stats": {
            "total_students": total_students,
            "high_students": good_count,
            "medium_students": 0,
            "low_students": low_count
        },
        "alert_stats": {
            "open_alerts": low_count,
            "open_critical": low_count,
            "open_warning": 0
        },
        "prediction_stats": {
            "total_predictions": total_marks_count,
            "avg_confidence": 1.0
        },
        "recent_critical_alerts": [
            {
                "id": i,
                "alert_type": "Low Performance",
                "message": f"Scored {r.get('marks_obtained', 0)}/{r.get('max_marks', 0)} in {r.get('subject_name', '')} ({r.get('assessment_name', '')})",
                "student_id": r.get("registration_number", ""),
                "created_at": str(r.get("created_at", ""))
            }
            for i, r in enumerate(recent_critical)
        ],
        "at_risk_students": [
            {
                "id": r.get("registration_number", ""),
                "name": r.get("registration_number", ""),
                "performance": "Low",
                "attendance": 0,
                "study_hours": 0
            }
            for r in recent_critical
        ]
    }
