# -*- coding: utf-8 -*-
"""
database/models/prediction_log.py
-----------------------------------
MongoDB operations for the prediction_logs collection.
"""
from __future__ import annotations
from datetime import datetime
from database.db import get_db, get_next_id


class PredictionLogModel:
    COL = "prediction_logs"

    @staticmethod
    def log(
        study_hours: float,
        attendance: float,
        previous_score: float,
        assignments: float,
        internal_marks: float,
        prediction: str,
        confidence: float,
        prob_high: float,
        prob_medium: float,
        prob_low: float,
        student_id: str | None = None,
        request_type: str = "single",
        ip_address: str | None = None,
    ) -> int:
        db = get_db()
        doc_id = get_next_id("prediction_logs_id")
        doc = {
            "id": doc_id,
            "student_id": student_id,
            "request_type": request_type,
            "study_hours": round(study_hours, 2),
            "attendance": round(attendance, 2),
            "previous_score": round(previous_score, 2),
            "assignments": round(assignments, 2),
            "internal_marks": round(internal_marks, 2),
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "prob_high": round(prob_high, 4),
            "prob_medium": round(prob_medium, 4),
            "prob_low": round(prob_low, 4),
            "ip_address": ip_address,
            "created_at": datetime.now(),
        }
        db[PredictionLogModel.COL].insert_one(doc)
        return doc_id

    @staticmethod
    def get_recent(limit: int = 50, prediction: str | None = None) -> list[dict]:
        db = get_db()
        query = {"prediction": prediction} if prediction else {}
        return list(db[PredictionLogModel.COL].find(query, {"_id": 0}).sort("created_at", -1).limit(limit))

    @staticmethod
    def get_by_student(student_id: str, limit: int = 20) -> list[dict]:
        db = get_db()
        return list(db[PredictionLogModel.COL].find(
            {"student_id": student_id}, {"_id": 0}
        ).sort("created_at", -1).limit(limit))

    @staticmethod
    def summary() -> dict:
        db = get_db()
        pipeline = [
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "high_count": {"$sum": {"$cond": [{"$eq": ["$prediction", "High"]}, 1, 0]}},
                "medium_count": {"$sum": {"$cond": [{"$eq": ["$prediction", "Medium"]}, 1, 0]}},
                "low_count": {"$sum": {"$cond": [{"$eq": ["$prediction", "Low"]}, 1, 0]}},
                "avg_confidence": {"$avg": "$confidence"},
                "last_prediction_date": {"$max": "$created_at"},
            }}
        ]
        result = list(db[PredictionLogModel.COL].aggregate(pipeline))
        if result:
            r = result[0]
            r.pop("_id", None)
            if r.get("avg_confidence") is not None:
                r["avg_confidence"] = round(r["avg_confidence"], 4)
            if r.get("last_prediction_date"):
                r["last_prediction_date"] = str(r["last_prediction_date"].date()) if hasattr(r["last_prediction_date"], "date") else str(r["last_prediction_date"])
            return r
        return {"total": 0, "high_count": 0, "medium_count": 0, "low_count": 0, "avg_confidence": 0, "last_prediction_date": None}
