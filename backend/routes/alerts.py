# -*- coding: utf-8 -*-
"""
backend/routes/alerts.py
-------------------------
REST endpoints for the alert_records table:

  GET  /api/alerts              - list alerts (filter: resolved, severity)
  GET  /api/alerts/summary      - open / resolved / severity counts
  GET  /api/alerts/<id>         - single alert
  POST /api/alerts/<id>/resolve - mark an alert resolved
  GET  /api/alerts/student/<id> - all alerts for a student
"""
from flask import Blueprint, request, jsonify
from database.models.alert import AlertModel

alerts_bp = Blueprint("alerts", __name__, url_prefix="/api/alerts")


@alerts_bp.route("", methods=["GET"])
def list_alerts():
    """
    GET /api/alerts?resolved=false&severity=critical&limit=50
    """
    resolved_param = request.args.get("resolved")
    severity       = request.args.get("severity")
    limit          = min(200, max(1, int(request.args.get("limit", 50))))

    resolved = None
    if resolved_param is not None:
        resolved = resolved_param.lower() in ("true", "1", "yes")

    try:
        rows = AlertModel.get_all(resolved=resolved, severity=severity, limit=limit)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    # Convert datetimes to strings for JSON
    for r in rows:
        for k in ("created_at", "resolved_at"):
            if r.get(k):
                r[k] = str(r[k])

    return jsonify({"success": True, "count": len(rows), "alerts": rows}), 200


@alerts_bp.route("/summary", methods=["GET"])
def alerts_summary():
    """GET /api/alerts/summary"""
    try:
        data = AlertModel.summary()
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    return jsonify({"success": True, **{k: int(v or 0) for k, v in data.items()}}), 200


@alerts_bp.route("/student/<student_id>", methods=["GET"])
def student_alerts(student_id: str):
    """GET /api/alerts/student/<id>"""
    try:
        from database.models.alert import AlertModel
        rows = AlertModel.get_by_student(student_id)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    for r in rows:
        for k in ("created_at", "resolved_at"):
            if r.get(k):
                r[k] = str(r[k])

    return jsonify({"success": True, "student_id": student_id,
                    "count": len(rows), "alerts": rows}), 200


@alerts_bp.route("/<int:alert_id>/resolve", methods=["POST"])
def resolve_alert(alert_id: int):
    """POST /api/alerts/<id>/resolve  Body: {"resolved_by": "teacher_name"}"""
    data        = request.get_json(silent=True) or {}
    resolved_by = data.get("resolved_by", "api")

    try:
        ok = AlertModel.resolve(alert_id, resolved_by=resolved_by)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    if not ok:
        return jsonify({"success": False,
                        "error": f"Alert {alert_id} not found or already resolved."}), 404

    return jsonify({"success": True,
                    "message": f"Alert {alert_id} resolved by '{resolved_by}'."}), 200
