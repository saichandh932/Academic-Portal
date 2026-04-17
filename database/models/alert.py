# -*- coding: utf-8 -*-
"""
database/models/alert.py
-------------------------
MongoDB operations for the alert_records collection.
"""
from __future__ import annotations
from datetime import datetime
from database.db import get_db, get_next_id
from backend.config import Config


class AlertModel:
    COL = "alert_records"

    @staticmethod
    def create(
        alert_type: str,
        severity: str,
        message: str,
        student_id: str | None = None,
        prediction_id: int | None = None,
        attendance: float | None = None,
        study_hours: float | None = None,
        prediction: str | None = None,
        confidence: float | None = None,
    ) -> int:
        db = get_db()
        doc_id = get_next_id("alert_records_id")
        doc = {
            "id": doc_id,
            "student_id": student_id,
            "prediction_id": prediction_id,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "attendance": attendance,
            "study_hours": study_hours,
            "prediction": prediction,
            "confidence": confidence,
            "is_resolved": 0,
            "resolved_at": None,
            "resolved_by": None,
            "created_at": datetime.now(),
        }
        db[AlertModel.COL].insert_one(doc)
        return doc_id

    @staticmethod
    def evaluate_and_raise(
        features: dict,
        prediction: str,
        confidence: float,
        prediction_id: int | None = None,
        student_id: str | None = None,
    ) -> list[int]:
        alerts_created = []
        risk_factors = 0

        att = features.get("attendance", 0)
        hrs = features.get("study_hours", 0)
        prev = features.get("previous_score", 0)

        if prediction == "Low":
            aid = AlertModel.create(
                alert_type="low_performance", severity="critical",
                message=f"Student predicted LOW performance (confidence {confidence*100:.1f}%). Immediate academic support recommended.",
                student_id=student_id, prediction_id=prediction_id,
                attendance=att, study_hours=hrs, prediction=prediction, confidence=confidence,
            )
            alerts_created.append(aid)
            risk_factors += 1

        if att < Config.ALERT_LOW_ATTENDANCE:
            aid = AlertModel.create(
                alert_type="low_attendance", severity="warning",
                message=f"Attendance is {att:.1f}%, below threshold of {Config.ALERT_LOW_ATTENDANCE}%.",
                student_id=student_id, prediction_id=prediction_id,
                attendance=att, study_hours=hrs, prediction=prediction, confidence=confidence,
            )
            alerts_created.append(aid)
            risk_factors += 1

        if hrs < Config.ALERT_LOW_STUDY_HOURS:
            aid = AlertModel.create(
                alert_type="low_study_hours", severity="warning",
                message=f"Study hours ({hrs:.1f} h/day) are below minimum threshold of {Config.ALERT_LOW_STUDY_HOURS} h/day.",
                student_id=student_id, prediction_id=prediction_id,
                attendance=att, study_hours=hrs, prediction=prediction, confidence=confidence,
            )
            alerts_created.append(aid)
            risk_factors += 1

        if prev < Config.ALERT_LOW_PREV_SCORE:
            aid = AlertModel.create(
                alert_type="low_previous_score", severity="info",
                message=f"Previous exam score ({prev:.1f}) is below threshold of {Config.ALERT_LOW_PREV_SCORE}.",
                student_id=student_id, prediction_id=prediction_id,
                attendance=att, study_hours=hrs, prediction=prediction, confidence=confidence,
            )
            alerts_created.append(aid)
            risk_factors += 1

        if risk_factors >= 3:
            aid = AlertModel.create(
                alert_type="multiple_risk_factors", severity="critical",
                message=f"Student has {risk_factors} simultaneous risk factors. Urgent intervention required.",
                student_id=student_id, prediction_id=prediction_id,
                attendance=att, study_hours=hrs, prediction=prediction, confidence=confidence,
            )
            alerts_created.append(aid)

        return alerts_created

    @staticmethod
    def get_all(resolved: bool | None = None, severity: str | None = None, limit: int = 50) -> list[dict]:
        db = get_db()
        query = {}
        if resolved is not None:
            query["is_resolved"] = 1 if resolved else 0
        if severity:
            query["severity"] = severity

        return list(db[AlertModel.COL].find(query, {"_id": 0}).sort("created_at", -1).limit(limit))

    @staticmethod
    def get_by_student(student_id: str, limit: int = 50) -> list[dict]:
        db = get_db()
        return list(db[AlertModel.COL].find(
            {"student_id": student_id}, {"_id": 0}
        ).sort("created_at", -1).limit(limit))

    @staticmethod
    def resolve(alert_id: int, resolved_by: str = "system") -> bool:
        db = get_db()
        result = db[AlertModel.COL].update_one(
            {"id": alert_id, "is_resolved": 0},
            {"$set": {
                "is_resolved": 1,
                "resolved_at": datetime.now(),
                "resolved_by": resolved_by
            }}
        )
        return result.modified_count > 0

    @staticmethod
    def summary() -> dict:
        db = get_db()
        pipeline = [
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "open": {"$sum": {"$cond": [{"$eq": ["$is_resolved", 0]}, 1, 0]}},
                "resolved": {"$sum": {"$cond": [{"$eq": ["$is_resolved", 1]}, 1, 0]}},
                "critical": {"$sum": {"$cond": [{"$eq": ["$severity", "critical"]}, 1, 0]}},
                "warning": {"$sum": {"$cond": [{"$eq": ["$severity", "warning"]}, 1, 0]}},
                "info": {"$sum": {"$cond": [{"$eq": ["$severity", "info"]}, 1, 0]}},
            }}
        ]
        result = list(db[AlertModel.COL].aggregate(pipeline))
        if result:
            r = result[0]
            r.pop("_id", None)
            return r
        return {"total": 0, "open": 0, "resolved": 0, "critical": 0, "warning": 0, "info": 0}
