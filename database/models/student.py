# -*- coding: utf8 -*-
"""
database/models/student.py
---------------------------
MongoDB CRUD operations for students, marks, attendance, and locks.
"""
from __future__ import annotations
from datetime import datetime
from database.db import get_db, get_next_id


class StudentModel:
    COL = "students"

    @staticmethod
    def create(data: dict) -> str:
        db = get_db()
        placeholders = [
            "registration_number", "name", "email", "password",
            "course", "branch", "year", "semester", "section", "gender", "dob",
            "study_hours", "attendance", "previous_score",
            "assignments", "internal_marks", "performance"
        ]
        doc = {k: data.get(k) for k in placeholders}
        if doc["name"] is None: doc["name"] = "Unknown"
        if doc["performance"] is None: doc["performance"] = "Low"
        for k in ["study_hours", "attendance", "previous_score", "assignments", "internal_marks"]:
            if doc[k] is None: doc[k] = 0.0

        now = datetime.now()
        doc["created_at"] = now
        doc["updated_at"] = now

        db[StudentModel.COL].update_one(
            {"registration_number": doc["registration_number"]},
            {"$set": doc},
            upsert=True
        )
        return doc["registration_number"]

    @staticmethod
    def update(registration_number: str, data: dict) -> bool:
        if not data:
            return False
        data["updated_at"] = datetime.now()
        db = get_db()
        result = db[StudentModel.COL].update_one(
            {"registration_number": registration_number},
            {"$set": data}
        )
        return result.modified_count > 0 or result.matched_count > 0

    @staticmethod
    def delete(registration_number: str) -> bool:
        db = get_db()
        result = db[StudentModel.COL].delete_one({"registration_number": registration_number})
        return result.deleted_count > 0

    @staticmethod
    def bulk_create(registration_ids: list[str]) -> tuple[int, list[str]]:
        if not registration_ids:
            return 0, []
        db = get_db()
        from pymongo import UpdateOne
        ops = [
            UpdateOne(
                {"registration_number": rid},
                {"$setOnInsert": {
                    "registration_number": rid,
                    "email": "student@gmail.com",
                    "password": rid,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }},
                upsert=True
            ) for rid in registration_ids
        ]
        result = db[StudentModel.COL].bulk_write(ops)
        return result.upserted_count, registration_ids

    @staticmethod
    def get_all() -> list[dict]:
        db = get_db()
        return list(db[StudentModel.COL].find({}, {"_id": 0}).sort("registration_number", 1))

    @staticmethod
    def verify_login(registration_number: str, password: str) -> bool:
        db = get_db()
        row = db[StudentModel.COL].find_one(
            {"registration_number": registration_number},
            {"password": 1}
        )
        if row and row.get("password") == password:
            return True
        return False

    @staticmethod
    def get_email(registration_number: str) -> str | None:
        db = get_db()
        row = db[StudentModel.COL].find_one(
            {"registration_number": registration_number},
            {"email": 1}
        )
        return row.get("email") if row else None

    @staticmethod
    def get_stats() -> dict:
        db = get_db()
        total = db[StudentModel.COL].count_documents({})

        pipeline = [
            {"$group": {"_id": "$performance", "count": {"$sum": 1}}}
        ]
        class_counts = {r["_id"]: r["count"] for r in db[StudentModel.COL].aggregate(pipeline)}

        pipeline_avg = [
            {"$group": {
                "_id": None,
                "avg_attendance": {"$avg": "$attendance"},
                "avg_study_hours": {"$avg": "$study_hours"},
                "avg_previous_score": {"$avg": "$previous_score"},
                "avg_internal_marks": {"$avg": "$internal_marks"},
                "avg_assignments": {"$avg": "$assignments"},
            }}
        ]
        overall_list = list(db[StudentModel.COL].aggregate(pipeline_avg))
        overall = overall_list[0] if overall_list else {}
        overall.pop("_id", None)

        return {
            "total": total,
            "class_counts": class_counts,
            "overall": {k: float(v) if v is not None else 0 for k, v in overall.items()}
        }


class StudentMarksModel:
    COL = "student_marks"

    @staticmethod
    def clear_assessment(subject_name: str, assessment_name: str):
        db = get_db()
        db[StudentMarksModel.COL].delete_many({
            "subject_name": subject_name,
            "assessment_name": assessment_name
        })

    @staticmethod
    def insert_mark(registration_number: str, subject_name: str, assessment_name: str, marks_obtained: float, max_marks: float) -> int:
        percentage = (marks_obtained / max_marks) * 100 if max_marks > 0 else 0
        status = "Low" if percentage < 40 else "Good"
        now = datetime.now()

        db = get_db()
        db[StudentMarksModel.COL].update_one(
            {
                "registration_number": registration_number,
                "subject_name": subject_name,
                "assessment_name": assessment_name
            },
            {"$set": {
                "marks_obtained": marks_obtained,
                "max_marks": max_marks,
                "performance_status": status,
                "updated_at": now
            },
            "$setOnInsert": {
                "created_at": now
            }},
            upsert=True
        )

        StudentMarksModel.update_student_global_performance(registration_number)
        return 0

    @staticmethod
    def update_student_global_performance(registration_number: str):
        db = get_db()
        pipeline = [
            {"$match": {"registration_number": registration_number}},
            {"$project": {"pct": {"$multiply": [{"$divide": ["$marks_obtained", "$max_marks"]}, 100]}}},
            {"$group": {"_id": None, "avg_score": {"$avg": "$pct"}}}
        ]
        result = list(db[StudentMarksModel.COL].aggregate(pipeline))
        if result and result[0].get("avg_score") is not None:
            score = result[0]["avg_score"]
            if score >= 80: performance = "High"
            elif score >= 40: performance = "Medium"
            else: performance = "Low"
            db[StudentModel.COL].update_one(
                {"registration_number": registration_number},
                {"$set": {"internal_marks": round(score, 2), "performance": performance}}
            )

    @staticmethod
    def get_by_student(registration_number: str) -> list[dict]:
        db = get_db()
        return list(db[StudentMarksModel.COL].find(
            {"registration_number": registration_number},
            {"_id": 0}
        ).sort("created_at", -1))

    @staticmethod
    def get_all_marks() -> list[dict]:
        db = get_db()
        return list(db[StudentMarksModel.COL].find({}, {"_id": 0}).sort("created_at", -1))


class AssessmentLockModel:
    COL = "locked_assessments"

    @staticmethod
    def is_locked(subject_name: str, assessment_name: str) -> bool:
        db = get_db()
        return db[AssessmentLockModel.COL].find_one({
            "subject_name": subject_name,
            "assessment_name": assessment_name
        }) is not None

    @staticmethod
    def lock(subject_name: str, assessment_name: str) -> bool:
        db = get_db()
        try:
            db[AssessmentLockModel.COL].insert_one({
                "subject_name": subject_name,
                "assessment_name": assessment_name,
                "locked_at": datetime.now()
            })
            return True
        except Exception:
            return False

    @staticmethod
    def get_all_locks() -> list[dict]:
        db = get_db()
        return list(db[AssessmentLockModel.COL].find({}, {"_id": 0, "subject_name": 1, "assessment_name": 1}))


class AttendanceModel:
    COL = "attendance"

    @staticmethod
    def upload_attendance(subject_name: str, date_str: str, period: int, records: list[dict]) -> int:
        if not records:
            raise Exception("Cannot upload empty attendance records.")

        if AttendanceLockModel.is_locked(date_str, period):
            raise Exception(f"Attendance for {date_str} (Period {period}) is already finalized by another faculty.")

        db = get_db()
        from pymongo import UpdateOne
        ops = [
            UpdateOne(
                {
                    "registration_number": r["registration_number"],
                    "subject_name": subject_name,
                    "attendance_date": date_str,
                    "period": period
                },
                {"$set": {
                    "status": r["status"],
                    "recorded_at": datetime.now()
                }},
                upsert=True
            ) for r in records
        ]
        result = db[AttendanceModel.COL].bulk_write(ops)

        # Auto-lock
        try:
            db[AttendanceLockModel.COL].insert_one({
                "subject_name": subject_name,
                "attendance_date": date_str,
                "period": period,
                "locked_at": datetime.now()
            })
        except Exception:
            pass  # Already locked

        for r in records:
            AttendanceModel.update_student_global_attendance(r["registration_number"])

        return result.upserted_count + result.modified_count

    @staticmethod
    def update_student_global_attendance(registration_number: str):
        db = get_db()
        pipeline = [
            {"$match": {"registration_number": registration_number}},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "present": {"$sum": {"$cond": [{"$eq": ["$status", "Present"]}, 1, 0]}}
            }}
        ]
        result = list(db[AttendanceModel.COL].aggregate(pipeline))
        if result and result[0]["total"] > 0:
            percentage = (result[0]["present"] / result[0]["total"]) * 100
            db[StudentModel.COL].update_one(
                {"registration_number": registration_number},
                {"$set": {"attendance": round(percentage, 2)}}
            )

    @staticmethod
    def get_subject_attendance_summary(subject_name: str) -> list[dict]:
        db = get_db()
        pipeline = [
            {"$match": {"subject_name": subject_name}},
            {"$group": {
                "_id": "$registration_number",
                "total_classes": {"$sum": 1},
                "present_count": {"$sum": {"$cond": [{"$eq": ["$status", "Present"]}, 1, 0]}}
            }}
        ]
        rows = []
        for r in db[AttendanceModel.COL].aggregate(pipeline):
            total = r["total_classes"]
            present = r["present_count"]
            rows.append({
                "registration_number": r["_id"],
                "total_classes": total,
                "present_count": present,
                "percentage": round((present / total) * 100, 2) if total > 0 else 0
            })
        return rows

    @staticmethod
    def get_subject_attendance(subject_name: str, date_str: str = None, period: int = None) -> list[dict]:
        db = get_db()

        # 1. Try specific slot
        query = {"subject_name": subject_name, "attendance_date": date_str, "period": period}
        rows = list(db[AttendanceModel.COL].find(query, {"_id": 0}))
        if rows:
            return rows

        # 2. Heal: check if records exist in period 1 and re-align
        if date_str and period and period != 1:
            cnt = db[AttendanceModel.COL].count_documents({
                "subject_name": subject_name, "attendance_date": date_str, "period": 1
            })
            if cnt > 0:
                db[AttendanceModel.COL].update_many(
                    {"subject_name": subject_name, "attendance_date": date_str, "period": 1},
                    {"$set": {"period": period}}
                )
                rows = list(db[AttendanceModel.COL].find(query, {"_id": 0}))
                if rows:
                    return rows

        # 3. Global view: any records for this slot from any subject
        if date_str and period:
            global_rows = list(db[AttendanceModel.COL].find(
                {"attendance_date": date_str, "period": period}, {"_id": 0}
            ))
            if global_rows:
                actual_owner = global_rows[0]["subject_name"]
                for r in global_rows:
                    r["_locked_by"] = actual_owner
                return global_rows

        return []


class AttendanceLockModel:
    COL = "locked_attendance"

    @staticmethod
    def is_locked(date_str: str, period: int) -> bool:
        db = get_db()
        return db[AttendanceLockModel.COL].find_one({
            "attendance_date": date_str, "period": period
        }) is not None

    @staticmethod
    def get_lock_owner(date_str: str, period: int) -> str | None:
        db = get_db()
        row = db[AttendanceLockModel.COL].find_one(
            {"attendance_date": date_str, "period": period},
            {"subject_name": 1}
        )
        return row.get("subject_name") if row else None

    @staticmethod
    def get_all_locks(subject_name: str = None) -> list[dict]:
        db = get_db()
        query = {"subject_name": subject_name} if subject_name else {}
        return list(db[AttendanceLockModel.COL].find(query, {"_id": 0, "attendance_date": 1, "period": 1}))
