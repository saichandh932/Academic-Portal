# -*- coding: utf-8 -*-
"""
backend/routes/db_students.py
------------------------------
REST endpoints for the Gradebook System (MongoDB version)
"""
from flask import Blueprint, request, jsonify
from database.models.student import StudentModel, StudentMarksModel, AssessmentLockModel
from database.models.password_reset import PasswordResetModel
from database.models.admin import AdminModel
from database.db import get_db
import os

db_bp = Blueprint("db_students", __name__, url_prefix="/api/db")

def _serialize(data):
    """Helper to convert database rows into JSON-serializable formats."""
    from decimal import Decimal
    from datetime import datetime, date
    from bson import ObjectId

    def convert(val):
        if isinstance(val, Decimal): return float(val)
        if isinstance(val, (datetime, date)): return val.isoformat()
        if isinstance(val, ObjectId): return str(val)
        return val

    if isinstance(data, list):
        return [{k: convert(v) for k, v in row.items()} for row in data]
    if isinstance(data, dict):
        return {k: convert(v) for k, v in data.items()}
    return data

@db_bp.route("/setup_db", methods=["GET"])
def setup_db():
    try:
        db = get_db()
        
        # Create indexes
        db["students"].create_index("registration_number", unique=True)
        db["admins"].create_index("username", unique=True)
        db["student_marks"].create_index(
            [("registration_number", 1), ("subject_name", 1), ("assessment_name", 1)],
            unique=True
        )
        db["attendance"].create_index(
            [("registration_number", 1), ("subject_name", 1), ("attendance_date", 1), ("period", 1)],
            unique=True
        )
        db["locked_assessments"].create_index(
            [("subject_name", 1), ("assessment_name", 1)],
            unique=True
        )
        db["locked_attendance"].create_index(
            [("attendance_date", 1), ("period", 1)],
            unique=True
        )

        # Initialize Admin Accounts for all subjects
        subjects = [
            "SE", "PADCOM", "CNS", "CLSA", "IIC", "SE Lab", "CNS Lab",
            "ML Lab", "IT Lab", "QALR", "ML", "IT", "IDP-II", "Training (TRG)"
        ]
        admins_list = [
            {"username": f"admin_{s.replace(' ', '_').replace('-', '_')}", "password": "password", "assigned_subject": s}
            for s in subjects
        ]
        admins_list.append({"username": "admin", "password": "password", "assigned_subject": "SE"})
        AdminModel.bulk_create(admins_list)

        return jsonify({"success": True, "message": "Database Setup Complete with Subject-Specific Admins!"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── List students ──────────────────────────────────────────────────────────────
@db_bp.route("/students", methods=["GET"])
def list_students():
    try:
        performance = request.args.get("performance")
        per_page = int(request.args.get("per_page", 1000))

        db = get_db()
        query = {"performance": performance} if performance else {}
        rows = list(db["students"].find(query, {"_id": 0}).limit(per_page))
        total = db["students"].count_documents({})

    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    # Privacy Masking
    for row in rows:
        if 'name' in row and row['name']:
            row['name'] = f"Student {row['registration_number']}"

    return jsonify({
        "success": True,
        "total": total,
        "students": _serialize(rows),
    }), 200

# ── Create student ──────────────────────────────────────────────────────────────
@db_bp.route("/students", methods=["POST"])
def create_student():
    from backend.ml_model import ModelStore
    from backend.config import Config

    data = request.get_json(silent=True)
    if not data or "registration_number" not in data:
        return jsonify({"success": False, "error": "Missing registration_number."}), 400

    performance_auto = False
    prediction_result = None
    features = {col: float(data.get(col, 0)) for col in Config.FEATURE_COLS}

    if "performance" not in data:
        try:
            prediction_result = ModelStore.predict(features)
            data["performance"] = prediction_result["prediction"]
            performance_auto = True
        except Exception:
            data["performance"] = "Low"

    try:
        reg = StudentModel.create(data)

        alerts_raised = 0
        if prediction_result:
            from database.models.prediction_log import PredictionLogModel
            from database.models.alert import AlertModel

            pred_id = PredictionLogModel.log(
                **features,
                prediction=prediction_result["prediction"],
                confidence=prediction_result["confidence"],
                prob_high=prediction_result["probabilities"].get("High", 0),
                prob_medium=prediction_result["probabilities"].get("Medium", 0),
                prob_low=prediction_result["probabilities"].get("Low", 0),
                student_id=reg,
                request_type="onboarding",
                ip_address=request.remote_addr
            )

            alerts = AlertModel.evaluate_and_raise(
                features,
                prediction_result["prediction"],
                prediction_result["confidence"],
                prediction_id=pred_id,
                student_id=reg
            )
            alerts_raised = len(alerts)

        return jsonify({
            "success": True,
            "registration_number": reg,
            "performance": data["performance"],
            "performance_auto": performance_auto,
            "alerts_raised": alerts_raised
        }), 201
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

# ── Update student ──────────────────────────────────────────────────────────────
@db_bp.route("/students/<registration_number>", methods=["PUT"])
def update_student(registration_number: str):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Missing update data."}), 400
    try:
        success = StudentModel.update(registration_number, data)
        return jsonify({"success": success}), 200 if success else 404
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

# ── Delete student ──────────────────────────────────────────────────────────────
@db_bp.route("/students/<registration_number>", methods=["DELETE"])
def delete_student(registration_number: str):
    try:
        success = StudentModel.delete(registration_number)
        return jsonify({"success": success}), 200 if success else 404
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

# ── Student Login ──────────────────────────────────────────────────────────────
@db_bp.route("/students/login", methods=["POST"])
def login_student():
    data = request.get_json(silent=True)
    if not data or "id" not in data or "password" not in data:
        return jsonify({"success": False, "error": "Missing id or password."}), 400
    try:
        valid = StudentModel.verify_login(data["id"], data["password"])
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    if not valid:
        return jsonify({"success": False, "error": "Invalid registration number or password."}), 401
    return jsonify({"success": True, "message": "Login successful"}), 200

# ── Upload Assessment Marks ───────────────────────────────────────────────────
@db_bp.route("/marks/upload", methods=["POST"])
def upload_marks():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Missing payload."}), 400

    subject_name = data.get("subject_name")
    assessment_name = data.get("assessment_name")
    max_marks = float(data.get("max_marks", 100))
    grades = data.get("grades", [])
    topics = data.get("topics", [])  # NEW: list of syllabus topics covered in this assessment

    if not subject_name or not assessment_name or not grades:
        return jsonify({"success": False, "error": "Missing required gradebook fields."}), 400

    if AssessmentLockModel.is_locked(subject_name, assessment_name):
        return jsonify({"success": False, "error": f"Assessment '{assessment_name}' is permanently LOCKED and cannot be modified."}), 403

    inserted = 0
    try:
        StudentMarksModel.clear_assessment(subject_name, assessment_name)

        for grade in grades:
            marks = float(grade["marks_obtained"])
            reg_num = grade["registration_number"]

            if marks > max_marks:
                return jsonify({"success": False, "error": f"Mark {marks} exceeds maximum {max_marks} for student {reg_num}"}), 400

            StudentMarksModel.insert_mark(
                registration_number=reg_num,
                subject_name=subject_name,
                assessment_name=assessment_name,
                marks_obtained=marks,
                max_marks=max_marks,
                topics=topics
            )
            inserted += 1

        # ── ML Re-Prediction for all affected students ────────────────────────
        repredicted = 0
        try:
            from backend.services.feature_extractor import extract_features
            from backend.ml_model import ModelStore
            from database.models.prediction_log import PredictionLogModel

            affected_reg_nums = list({g["registration_number"] for g in grades})
            for reg_num in affected_reg_nums:
                live_features, _ = extract_features(reg_num)
                res = ModelStore.predict(live_features)

                # Update student performance label in DB
                from database.db import get_db as _get_db
                from datetime import datetime as _dt
                _get_db()["students"].update_one(
                    {"registration_number": reg_num},
                    {"$set": {
                        "performance":    res["prediction"],
                        "internal_marks": round(live_features["internal_marks"], 2),
                        "attendance":     round(live_features["attendance"], 2),
                        "updated_at":     _dt.now(),
                    }}
                )
                # Log the prediction
                PredictionLogModel.log(
                    **live_features,
                    prediction   = res["prediction"],
                    confidence   = res["confidence"],
                    prob_high    = res["probabilities"].get("High",   0),
                    prob_medium  = res["probabilities"].get("Medium", 0),
                    prob_low     = res["probabilities"].get("Low",    0),
                    student_id   = reg_num,
                    request_type = "marks_upload",
                )

                # ── Smart ML Risk Alert ──────────────────────────────────────
                try:
                    from backend.services.grade_predictor import predict_grade
                    from backend.services.explainer      import explain_prediction
                    from backend.services.email_service  import EmailService

                    grade_result = predict_grade(live_features)
                    risk_score   = grade_result["risk_score"]
                    risk_level   = grade_result["risk_level"]

                    if risk_score >= 45:  # high or critical threshold
                        explanation = explain_prediction(
                            live_features, res["prediction"], res["probabilities"]
                        )
                        recommendations = explanation.get("recommendations", [])

                        # Fetch student email
                        student_doc = _get_db()["students"].find_one(
                            {"registration_number": reg_num}, {"email": 1}
                        )
                        student_email = (student_doc or {}).get("email", "")

                        if student_email:
                            EmailService.send_risk_alert(
                                student_email = student_email,
                                student_id    = reg_num,
                                risk_score    = risk_score,
                                risk_level    = risk_level,
                                grade_letter  = grade_result["grade_letter"],
                                expected_pct  = grade_result["expected_percentage"],
                                prediction    = res["prediction"],
                                recommendations = recommendations,
                            )
                            print(f"[ML ALERT] Risk alert sent → {reg_num} (score={risk_score}, level={risk_level})")
                except Exception:
                    pass  # Never let email failure break anything

                repredicted += 1
        except Exception:
            pass  # Re-prediction must never break the marks upload

        return jsonify({
            "success":     True,
            "message":     f"Successfully recorded {inserted} marks.",
            "repredicted": repredicted,
        }), 201
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

# ── Get Prediction History ───────────────────────────────────────────────────
@db_bp.route("/students/<registration_number>/history", methods=["GET"])
def get_student_history(registration_number: str):
    try:
        from database.models.prediction_log import PredictionLogModel
        rows = PredictionLogModel.get_by_student(registration_number)
        return jsonify({"success": True, "count": len(rows), "history": _serialize(rows)}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

# ── Prediction Logs ───────────────────────────────────────────────────────────
@db_bp.route("/predictions", methods=["GET"])
def get_prediction_logs():
    try:
        from database.models.prediction_log import PredictionLogModel
        limit = int(request.args.get("limit", 50))
        rows = PredictionLogModel.get_recent(limit=limit)
        return jsonify({"success": True, "count": len(rows), "logs": _serialize(rows)}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

@db_bp.route("/predictions/summary", methods=["GET"])
def get_prediction_summary():
    try:
        from database.models.prediction_log import PredictionLogModel
        sum_data = PredictionLogModel.summary()
        return jsonify({"success": True, **sum_data}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

# ── Get Student by Registration Number ────────────────────────────────────────
@db_bp.route("/students/reg/<registration_number>", methods=["GET"])
def get_student_by_reg(registration_number: str):
    try:
        db = get_db()
        row = db["students"].find_one(
            {"registration_number": registration_number},
            {"_id": 0}
        )
        if not row:
            return jsonify({"success": False, "error": "Student not found"}), 404
        return jsonify({"success": True, "student": _serialize(row)}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

# ── Get Student Stats ─────────────────────────────────────────────────────────
@db_bp.route("/students/stats", methods=["GET"])
def get_student_stats():
    try:
        stats = StudentModel.get_stats()
        return jsonify({"success": True, **stats}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

# ── Get Student Marks ─────────────────────────────────────────────────────────
@db_bp.route("/students/<registration_number>/marks", methods=["GET"])
def get_student_marks(registration_number: str):
    try:
        rows = StudentMarksModel.get_by_student(registration_number)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    return jsonify({"success": True, "total": len(rows), "marks": _serialize(rows)}), 200

# ── Get All Marks (for Dashboard) ─────────────────────────────────────────────
@db_bp.route("/marks", methods=["GET"])
def get_all_marks():
    try:
        rows = StudentMarksModel.get_all_marks()
        locks = AssessmentLockModel.get_all_locks()
        return jsonify({"success": True, "total": len(rows), "marks": _serialize(rows), "locks": locks}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

@db_bp.route("/assessments/lock", methods=["POST"], strict_slashes=False)
def lock_assessment():
    data = request.get_json(silent=True)
    if not data or "subject_name" not in data or "assessment_name" not in data:
        return jsonify({"success": False, "error": "Missing subject or assessment name."}), 400
    try:
        success = AssessmentLockModel.lock(data["subject_name"], data["assessment_name"])
        if success:
            return jsonify({"success": True, "message": "Assessment permanently locked."}), 200
        else:
            return jsonify({"success": False, "error": "Already locked or failed to lock."}), 400
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

@db_bp.route("/marks/notify-student", methods=["POST"], strict_slashes=False)
def notify_student():
    from backend.services.email_service import EmailService
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Missing payload."}), 400
    reg_num = data.get("registration_number")
    subject_name = data.get("subject_name")
    assessment_name = data.get("assessment_name")
    marks_obtained = data.get("marks_obtained")
    max_marks = data.get("max_marks")
    if not reg_num or not subject_name or not assessment_name:
        return jsonify({"success": False, "error": "Missing student or assessment info."}), 400
    try:
        student_email = StudentModel.get_email(reg_num)
        if not student_email:
            return jsonify({"success": False, "error": f"Email not found for student {reg_num}"}), 404
        success, err_msg = EmailService.send_low_performance_alert(
            student_email=student_email, student_id=reg_num,
            subject_name=subject_name, assessment_name=assessment_name,
            marks_obtained=marks_obtained, max_marks=max_marks
        )
        if success:
            return jsonify({"success": True, "message": f"Alert email sent to {reg_num}!"}), 200
        else:
            return jsonify({"success": False, "error": f"Email Error: {err_msg}"}), 500
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

@db_bp.route("/marks/notify-all", methods=["POST"], strict_slashes=False)
def notify_all():
    from backend.services.email_service import EmailService
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Missing payload."}), 400
    subject_name = data.get("subject_name")
    assessment_name = data.get("assessment_name")
    students_to_notify = data.get("students", [])
    if not students_to_notify:
        return jsonify({"success": False, "error": "No students provided for notification."}), 400

    sent_count = 0
    errors = []
    try:
        for s in students_to_notify:
            reg_num = s.get("registration_number")
            marks = s.get("marks_obtained")
            m_max = s.get("max_marks")
            email = StudentModel.get_email(reg_num)
            if not email:
                errors.append(f"Email not found for {reg_num}")
                continue
            success, _ = EmailService.send_low_performance_alert(
                student_email=email, student_id=reg_num,
                subject_name=subject_name, assessment_name=assessment_name,
                marks_obtained=marks, max_marks=m_max
            )
            if success: sent_count += 1
            else: errors.append(f"Failed to notify {reg_num}")
        return jsonify({"success": True, "message": f"Bulk notification complete. Sent: {sent_count}, Failed: {len(errors)}", "errors": errors}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

# ── Password Resets ───────────────────────────────────────────────────────────
@db_bp.route("/password/forgot", methods=["POST"], strict_slashes=False)
def password_forgot():
    data = request.get_json(silent=True)
    if not data or not data.get("registration_number"):
        return jsonify({"success": False, "error": "Registration ID is required."}), 400
    reg_num = data["registration_number"]
    role = data.get("role", "Student")
    try:
        email = None
        if role == "Student":
            email = StudentModel.get_email(reg_num)
        else:
            email = AdminModel.get_email(reg_num)
        if not email:
            return jsonify({"success": False, "error": f"Account not found for ID {reg_num}"}), 404
        token = PasswordResetModel.create_token(reg_num, role)
        if not token:
            return jsonify({"success": False, "error": "Internal server error generating token."}), 500
        from backend.services.email_service import EmailService
        success, err = EmailService.send_password_reset_email(email, reg_num, token)
        if success:
            return jsonify({"success": True, "message": f"Reset link dispatched to {email}"}), 200
        else:
            return jsonify({"success": False, "error": f"Email dispatch failed: {err}"}), 500
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

@db_bp.route("/password/reset", methods=["POST"], strict_slashes=False)
def password_reset():
    data = request.get_json(silent=True)
    if not data or not data.get("token") or not data.get("password"):
        return jsonify({"success": False, "error": "Token and password are required."}), 400
    token = data["token"]
    new_password = data["password"]
    try:
        res = PasswordResetModel.verify_token(token)
        if not res:
            return jsonify({"success": False, "error": "Invalid or expired reset token."}), 400
        reg_num, role = res
        updated = False
        if role == "Student":
            updated = StudentModel.update(reg_num, {"password": new_password})
        else:
            updated = AdminModel.update_password(reg_num, new_password)
        if updated:
            PasswordResetModel.delete_token(token)
            return jsonify({"success": True, "message": "Password updated successfully! You can now log in."}), 200
        else:
            return jsonify({"success": False, "error": "Failed to update record."}), 500
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
