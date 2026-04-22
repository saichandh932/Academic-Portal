# -*- coding: utf8 -*-
"""
backend/routes/attendance.py
----------------------------
Endpoints for managing student attendance (MongoDB version).
"""
from flask import Blueprint, request, jsonify
from database.models.student import AttendanceModel, AttendanceLockModel, StudentModel
from backend.services.email_service import EmailService
from datetime import datetime, timedelta

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/db/attendance")

# Institutional Timetable
PERIOD_TIMINGS = {
    1: "08:15", 2: "09:05", 3: "10:10", 4: "11:00",
    5: "11:50", 6: "13:40", 7: "14:30", 8: "15:30"
}

@attendance_bp.route("/upload", methods=["POST"], strict_slashes=False)
def upload_attendance():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Missing payload"}), 400

    subject = data.get("subject") or data.get("subject_name")
    date_str = data.get("date")
    period = int(data.get("period", 1))
    records = data.get("records", [])

    if not subject or not date_str or not records:
        return jsonify({"success": False, "error": f"Missing required fields (subject={bool(subject)}, date={bool(date_str)}, records={bool(records)})"}), 400

    # 8-Hour Constraint Logic
    try:
        start_time_str = PERIOD_TIMINGS.get(period, "08:00")
        class_dt = datetime.strptime(f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M")
        now = datetime.now()

        if now > (class_dt + timedelta(hours=8)):
            diff = now - class_dt
            hours_passed = int(diff.total_seconds() // 3600)
            return jsonify({
                "success": False,
                "error": f"Submission period expired. Period {period} started at {start_time_str} ({hours_passed}h ago). The 8-hour window is closed."
            }), 403
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400

    try:
        now = datetime.now()
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        if selected_date > now.date():
            return jsonify({"success": False, "error": "Cannot post attendance for future dates."}), 400

        if (now.date() - selected_date).days > 0:
            return jsonify({"success": False, "error": "Integrity Alert: Attendance must be posted on the same calendar day."}), 400

        count = AttendanceModel.upload_attendance(subject, date_str, period, records)

        return jsonify({
            "success": True,
            "message": f"Attendance finalized for {subject} (Period {period}).",
            "count": count
        }), 201
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

@attendance_bp.route("/dispatch_alerts", methods=["POST"], strict_slashes=False)
def dispatch_alerts():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Missing payload"}), 400

    subject = data.get("subject") or data.get("subject_name")
    date_str = data.get("date")
    period = int(data.get("period", 1))
    records = data.get("records", [])

    absent_records = [r for r in records if r.get('status') == 'Absent']
    dispatch_report = []
    
    if absent_records:
        absent_regs = [r['registration_number'] for r in absent_records]
        
        # MongoDB lookup for emails
        from database.db import get_db
        db = get_db()
        student_docs = db["students"].find(
            {"registration_number": {"$in": absent_regs}},
            {"registration_number": 1, "email": 1, "_id": 0}
        )
        student_emails = {doc["registration_number"]: doc.get("email") for doc in student_docs}

        for r in absent_records:
            r['email'] = student_emails.get(r['registration_number'])

        dispatch_report = EmailService.send_bulk_absence_alerts(absent_records, subject, date_str, period)

    alerted_list = [d.get("reg_num") for d in dispatch_report] if dispatch_report else []
    return jsonify({
        "success": True,
        "emails_dispatched": len(dispatch_report),
        "dispatch_details": dispatch_report,
        "alerted_students": alerted_list
    }), 200

@attendance_bp.route("/", methods=["GET"])
def get_attendance():
    subject = request.args.get("subject")
    date_str = request.args.get("date")
    period = request.args.get("period")

    if not subject:
        return jsonify({"success": False, "error": "Subject name is required."}), 400

    try:
        p_val = int(period) if period else None
        rows = AttendanceModel.get_subject_attendance(subject, date_str, p_val)

        for r in rows:
            if 'attendance_date' in r and r['attendance_date']:
                if hasattr(r['attendance_date'], 'strftime'):
                    r['attendance_date'] = r['attendance_date'].strftime("%Y-%m-%d")
            if 'recorded_at' in r and r['recorded_at']:
                if hasattr(r['recorded_at'], 'strftime'):
                    r['recorded_at'] = r['recorded_at'].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({"success": True, "records": rows}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

@attendance_bp.route("/locks", methods=["GET"])
def get_locks():
    subject = request.args.get("subject")
    if not subject:
        return jsonify({"success": False, "error": "Subject name is required."}), 400

    try:
        rows = AttendanceLockModel.get_all_locks()
        locked_slots = []
        for r in rows:
            d = r.get('attendance_date')
            if d:
                if hasattr(d, 'strftime'):
                    d = d.strftime("%Y-%m-%d")
                locked_slots.append({"date": d, "period": r.get('period', 1)})

        return jsonify({"success": True, "locked_slots": locked_slots}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

@attendance_bp.route("/summary/subject/<subject>", methods=["GET"])
def get_subject_summary(subject):
    try:
        rows = AttendanceModel.get_subject_attendance_summary(subject)
        return jsonify({"success": True, "summary": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@attendance_bp.route("/summary/student/<reg_id>", methods=["GET"])
def get_student_summary(reg_id):
    try:
        from database.db import get_db
        db = get_db()
        pipeline = [
            {"$match": {"registration_number": reg_id}},
            {"$group": {
                "_id": "$subject_name",
                "total_classes": {"$sum": 1},
                "present_count": {"$sum": {"$cond": [{"$eq": ["$status", "Present"]}, 1, 0]}}
            }}
        ]
        results = list(db["attendance"].aggregate(pipeline))
        rows = []
        for r in results:
            total = r["total_classes"]
            present = r["present_count"]
            rows.append({
                "subject_name": r["_id"],
                "total_classes": total,
                "present_count": present,
                "percentage": round((present / total) * 100, 2) if total > 0 else 0
            })
        return jsonify({"success": True, "summary": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
