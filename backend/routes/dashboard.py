# -*- coding: utf-8 -*-
"""
backend/routes/dashboard.py
-----------------------------
Dashboard endpoints (MongoDB version).
"""
from flask import Blueprint, jsonify, request

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("", methods=["GET"])
def dashboard():
    try:
        from backend.services.alert_engine import get_dashboard_data
        data = get_dashboard_data()
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    return jsonify({"success": True, **data}), 200


@dashboard_bp.route("/login", methods=["POST"])
def admin_login():
    body = request.get_json(silent=True) or {}
    username = body.get("username")
    password = body.get("password")

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password required"}), 400

    from database.models.admin import AdminModel
    assigned_subject = AdminModel.verify_credentials(username, password)

    if assigned_subject:
        return jsonify({
            "success": True,
            "message": f"Admin authenticated for {assigned_subject}",
            "assigned_subject": assigned_subject
        }), 200
    else:
        return jsonify({"success": False, "error": "Invalid admin credentials"}), 401


@dashboard_bp.route("/scan", methods=["POST"])
def trigger_scan():
    body = request.get_json(silent=True) or {}
    run_by = body.get("run_by", "api")
    try:
        from backend.services.alert_engine import batch_scan
        result = batch_scan(run_by=run_by)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    return jsonify({"success": True, **result}), 200


@dashboard_bp.route("/at-risk", methods=["GET"])
def at_risk_students():
    limit = min(100, max(1, int(request.args.get("limit", 20))))

    try:
        from database.db import get_db
        db = get_db()

        # MongoDB aggregation to find students with open alerts
        pipeline = [
            {"$match": {"is_resolved": 0}},
            {"$group": {
                "_id": "$student_id",
                "open_alert_count": {"$sum": 1},
                "max_severity": {"$max": "$severity"},
                "alert_types": {"$addToSet": "$alert_type"},
                "latest_alert_at": {"$max": "$created_at"}
            }},
            {"$sort": {"open_alert_count": -1, "latest_alert_at": -1}},
            {"$limit": limit}
        ]
        alert_groups = list(db["alert_records"].aggregate(pipeline))

        # Lookup student details
        result = []
        for ag in alert_groups:
            student_id = ag["_id"]
            student = db["students"].find_one(
                {"registration_number": student_id},
                {"_id": 0, "registration_number": 1, "name": 1, "performance": 1,
                 "study_hours": 1, "attendance": 1, "previous_score": 1,
                 "assignments": 1, "internal_marks": 1}
            )
            if student:
                row = {
                    "id": student.get("registration_number", student_id),
                    "name": student.get("name", "Unknown"),
                    "performance": student.get("performance", ""),
                    "study_hours": float(student.get("study_hours", 0) or 0),
                    "attendance": float(student.get("attendance", 0) or 0),
                    "previous_score": float(student.get("previous_score", 0) or 0),
                    "assignments": float(student.get("assignments", 0) or 0),
                    "internal_marks": float(student.get("internal_marks", 0) or 0),
                    "open_alert_count": ag["open_alert_count"],
                    "max_severity": ag["max_severity"],
                    "alert_types": ", ".join(ag["alert_types"]),
                    "latest_alert_at": str(ag["latest_alert_at"]) if ag["latest_alert_at"] else None
                }
                result.append(row)

    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    return jsonify({"success": True, "count": len(result), "students": result}), 200
