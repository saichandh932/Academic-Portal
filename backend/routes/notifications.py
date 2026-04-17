# -*- coding: utf-8 -*-
"""
backend/routes/notifications.py
---------------------------------
Email notification management endpoints (MongoDB version).
"""
from flask import Blueprint, request, jsonify
from backend.config import Config

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@notifications_bp.route("/config", methods=["GET"])
def email_config():
    recipients = [r.strip() for r in Config.ALERT_EMAIL_TO.split(",") if r.strip()]
    return jsonify({
        "success":       True,
        "email_enabled": Config.EMAIL_ENABLED,
        "smtp_host":     Config.SMTP_HOST,
        "smtp_port":     Config.SMTP_PORT,
        "smtp_use_tls":  Config.SMTP_USE_TLS,
        "smtp_user":     Config.SMTP_USER or "(not set)",
        "smtp_password": "***" if Config.SMTP_PASSWORD else "(not set)",
        "from_name":     Config.SMTP_FROM_NAME,
        "recipients":    recipients,
        "thresholds": {
            "low_attendance":  Config.ALERT_LOW_ATTENDANCE,
            "low_study_hours": Config.ALERT_LOW_STUDY_HOURS,
            "low_prev_score":  Config.ALERT_LOW_PREV_SCORE,
        },
    }), 200


@notifications_bp.route("/test", methods=["POST"])
def send_test():
    data = request.get_json(silent=True) or {}
    recipient = data.get("recipient", "").strip()

    if not recipient or "@" not in recipient:
        return jsonify({"success": False,
                        "error": "'recipient' must be a valid email address."}), 422

    from backend.services.email_service import send_test_email
    result = send_test_email(recipient)
    code = 200 if result["success"] else 502
    return jsonify({"success": result["success"], "message": result["message"]}), code


@notifications_bp.route("/send-alert", methods=["POST"])
def send_manual_alert():
    data     = request.get_json(silent=True) or {}
    alert_id = data.get("alert_id")

    if not alert_id:
        return jsonify({"success": False, "error": "'alert_id' is required."}), 422

    try:
        from database.db import get_db
        db = get_db()
        alert = db["alert_records"].find_one({"id": int(alert_id)}, {"_id": 0})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    if not alert:
        return jsonify({"success": False,
                        "error": f"Alert {alert_id} not found."}), 404

    features = {
        "attendance":  float(alert.get("attendance") or 0),
        "study_hours": float(alert.get("study_hours") or 0),
    }

    extra = []
    if data.get("recipient"):
        extra = [data["recipient"].strip()]

    from backend.services.email_service import send_alert_email
    sent = send_alert_email(
        alert_type        = alert["alert_type"],
        severity          = alert["severity"],
        message           = alert["message"],
        features          = features,
        prediction        = alert.get("prediction"),
        confidence        = float(alert["confidence"]) if alert.get("confidence") else None,
        extra_recipients  = extra,
    )

    if not sent:
        return jsonify({
            "success": False,
            "message": "Email not sent -- EMAIL_ENABLED is false or no recipients configured.",
        }), 200

    return jsonify({
        "success": True,
        "message": f"Alert email for alert #{alert_id} dispatched.",
    }), 200
