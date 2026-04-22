# -*- coding: utf-8 -*-
"""
backend/routes/predict.py
--------------------------
POST /api/predict              - predict single student performance
POST /api/predict/batch        - predict a list of students at once
GET  /api/predict/student/<id> - LIVE prediction from real MongoDB data + explanation
GET  /api/predict/trend/<id>   - prediction trend history for a student
GET  /api/predict/grade/<id>   - grade letter + at-risk score prediction
"""
from flask import Blueprint, request, jsonify
from backend.ml_model import ModelStore
from backend.config   import Config

predict_bp = Blueprint("predict", __name__, url_prefix="/api")


def _validate_features(data: dict) -> tuple:
    if not isinstance(data, dict):
        return None, "Data payload must be a dictionary."

    missing = [col for col in Config.FEATURE_COLS if col not in data]
    if missing:
        return None, f"Missing required fields: {missing}"

    features = {}
    for col in Config.FEATURE_COLS:
        try:
            val = float(data[col])
        except (ValueError, TypeError):
            return None, f"Field '{col}' must be a numeric value."
        features[col] = val

    # Soft domain checks
    if not (0 <= features["attendance"]     <= 100): return None, "attendance must be between 0 and 100."
    if not (0 <= features["previous_score"] <= 100): return None, "previous_score must be between 0 and 100."
    if not (0 <= features["assignments"]    <= 100): return None, "assignments must be between 0 and 100."
    if not (0 <= features["internal_marks"] <= 100): return None, "internal_marks must be between 0 and 100."
    if not (0 <= features["study_hours"]    <= 24):  return None, "study_hours must be between 0 and 24."

    return features, None


# ── Single prediction (manual features) ───────────────────────────────────────
@predict_bp.route("/predict", methods=["POST"])
def predict():
    """
    Predict the performance category for a single student.

    Request body (JSON):
      {
        "study_hours":     <float>,
        "attendance":      <float, 0-100>,
        "previous_score":  <float, 0-100>,
        "assignments":     <float, 0-100>,
        "internal_marks":  <float, 0-100>
      }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Request body must be JSON."}), 400

    features, err = _validate_features(data)
    if err:
        return jsonify({"success": False, "error": err}), 422

    try:
        result = ModelStore.predict(features)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    # Add explanation
    try:
        from backend.services.explainer import explain_prediction
        explanation = explain_prediction(features, result["prediction"], result["probabilities"])
    except Exception:
        explanation = None

    # Log to DB (silent)
    try:
        from database.models.prediction_log import PredictionLogModel
        from backend.services.alert_engine  import process_prediction
        pred_id = PredictionLogModel.log(
            **features,
            prediction   = result["prediction"],
            confidence   = result["confidence"],
            prob_high    = result["probabilities"].get("High",   0),
            prob_medium  = result["probabilities"].get("Medium", 0),
            prob_low     = result["probabilities"].get("Low",    0),
            request_type = "single",
            ip_address   = request.remote_addr,
        )
    except Exception:
        pass

    return jsonify({
        "success":       True,
        "prediction":    result["prediction"],
        "probabilities": result["probabilities"],
        "confidence":    result["confidence"],
        "explanation":   explanation,
        "input":         features,
    }), 200


# ── LIVE prediction from MongoDB data ─────────────────────────────────────────
@predict_bp.route("/predict/student/<registration_number>", methods=["GET"])
def predict_student_live(registration_number: str):
    """
    GET /api/predict/student/<id>

    Derives features LIVE from real MongoDB attendance & marks data,
    runs the ML model, returns prediction + full explanation + recommendations.
    """
    try:
        from backend.services.feature_extractor import extract_features
        features, meta = extract_features(registration_number)
    except Exception as exc:
        return jsonify({"success": False, "error": f"Feature extraction failed: {exc}"}), 500

    try:
        result = ModelStore.predict(features)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    try:
        from backend.services.explainer import explain_prediction
        explanation = explain_prediction(features, result["prediction"], result["probabilities"])
    except Exception as exc:
        explanation = {"error": str(exc)}

    # Log this live prediction
    try:
        from database.models.prediction_log import PredictionLogModel
        PredictionLogModel.log(
            **features,
            prediction   = result["prediction"],
            confidence   = result["confidence"],
            prob_high    = result["probabilities"].get("High",   0),
            prob_medium  = result["probabilities"].get("Medium", 0),
            prob_low     = result["probabilities"].get("Low",    0),
            student_id   = registration_number,
            request_type = "live",
            ip_address   = request.remote_addr,
        )
    except Exception:
        pass

    return jsonify({
        "success":           True,
        "registration_number": registration_number,
        "features_used":     features,
        "data_source_meta":  meta,
        "prediction":        result["prediction"],
        "probabilities":     result["probabilities"],
        "confidence":        result["confidence"],
        "explanation":       explanation,
    }), 200


# ── Prediction trend for a student ────────────────────────────────────────────
@predict_bp.route("/predict/trend/<registration_number>", methods=["GET"])
def predict_trend(registration_number: str):
    """
    GET /api/predict/trend/<id>

    Returns the prediction history for a student as a time series,
    allowing the frontend to render a trend/trajectory chart.
    """
    try:
        from database.models.prediction_log import PredictionLogModel
        limit = int(request.args.get("limit", 20))
        rows  = PredictionLogModel.get_by_student(registration_number, limit=limit)

        # Format for chart consumption
        trend = []
        for r in reversed(rows):  # oldest first for chart
            created = r.get("created_at")
            if hasattr(created, "isoformat"):
                created = created.isoformat()
            trend.append({
                "date":            str(created)[:10] if created else "unknown",
                "prediction":      r.get("prediction", ""),
                "confidence":      round(float(r.get("confidence", 0)), 4),
                "prob_high":       round(float(r.get("prob_high",   0)), 4),
                "prob_medium":     round(float(r.get("prob_medium", 0)), 4),
                "prob_low":        round(float(r.get("prob_low",    0)), 4),
                "internal_marks":  round(float(r.get("internal_marks", 0)), 2),
                "attendance":      round(float(r.get("attendance",    0)), 2),
                "request_type":    r.get("request_type", ""),
            })

        # Detect trend direction
        if len(trend) >= 2:
            first_high = trend[0]["prob_high"]
            last_high  = trend[-1]["prob_high"]
            delta      = last_high - first_high
            direction  = "improving" if delta > 0.05 else "declining" if delta < -0.05 else "stable"
        else:
            direction = "insufficient_data"

        return jsonify({
            "success":              True,
            "registration_number":  registration_number,
            "trend":                trend,
            "trend_direction":      direction,
            "total_predictions":    len(trend),
        }), 200

    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ── Grade letter + At-Risk score prediction ────────────────────────────────────
@predict_bp.route("/predict/grade/<registration_number>", methods=["GET"])
def predict_grade(registration_number: str):
    """
    GET /api/predict/grade/<id>

    Returns:
      - expected_percentage  : predicted final semester score (Ridge Regression)
      - grade_letter         : S | A | B | C | D | E | F  (Vignan scale)
      - grade_points         : GPA points on 10-scale
      - risk_score           : 0–100 composite at-risk score
      - risk_level           : safe | moderate | high | critical
      - risk_color           : hex colour for UI badge
      - grade_table          : full grading scale with predicted grade highlighted
    """
    try:
        from backend.services.feature_extractor import extract_features
        features, meta = extract_features(registration_number)
    except Exception as exc:
        return jsonify({"success": False, "error": f"Feature extraction failed: {exc}"}), 500

    try:
        from backend.services.grade_predictor import predict_grade as _predict_grade
        result = _predict_grade(features)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    return jsonify({
        "success":              True,
        "registration_number":  registration_number,
        **result,
    }), 200


# ── Attendance Dropout Predictor ───────────────────────────────────────────────
@predict_bp.route("/predict/attendance/<registration_number>", methods=["GET"])
def predict_attendance_dropout(registration_number: str):
    """
    GET /api/predict/attendance/<id>
    Predicts if the student will drop below the 75% attendance threshold.
    """
    try:
        from backend.services.attendance_predictor import predict_attendance_for_student
        result = predict_attendance_for_student(registration_number)
        return jsonify(result), 200 if result.get("success") else 404
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


# ── Class Risk Leaderboard ─────────────────────────────────────────────────────
@predict_bp.route("/predict/leaderboard/risk", methods=["GET"])
def predict_risk_leaderboard():
    """
    GET /api/predict/leaderboard/risk
    Returns all students sorted by at-risk score (highest risk first).
    """
    try:
        from database.db import get_db
        from backend.services.feature_extractor import extract_features
        from backend.services.grade_predictor import predict_grade
        
        students = list(get_db()["students"].find({}, {"registration_number": 1, "name": 1, "email": 1, "_id": 0}))
        
        leaderboard = []
        for s in students:
            reg_num = s["registration_number"]
            try:
                features, _ = extract_features(reg_num)
                grade_res   = predict_grade(features)
                leaderboard.append({
                    "registration_number": reg_num,
                    "name":                s.get("name", "Unknown"),
                    "email":               s.get("email", ""),
                    "risk_score":          grade_res["risk_score"],
                    "risk_level":          grade_res["risk_level"],
                    "expected_pct":        grade_res["expected_percentage"],
                    "grade_letter":        grade_res["grade_letter"],
                })
            except Exception:
                continue  # skip if feature extraction fails (e.g. no data)
                
        # Sort by risk_score descending
        leaderboard.sort(key=lambda x: x["risk_score"], reverse=True)
        
        return jsonify({
            "success": True,
            "total": len(leaderboard),
            "leaderboard": leaderboard
        }), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

# ── Batch prediction ───────────────────────────────────────────────────────────
@predict_bp.route("/predict/batch", methods=["POST"])
def predict_batch():
    """
    POST /api/predict/batch
    Predict performance for multiple students in a single call.
    """
    data = request.get_json(silent=True)
    if not data or "students" not in data:
        return jsonify({"success": False,
                        "error": "Body must be JSON with a 'students' list."}), 400

    students = data["students"]
    if not isinstance(students, list) or len(students) == 0:
        return jsonify({"success": False,
                        "error": "'students' must be a non-empty list."}), 422

    results, errors = [], []

    for i, student in enumerate(students):
        features, err = _validate_features(student)
        if err:
            errors.append({"index": i, "error": err})
            continue
        try:
            res = ModelStore.predict(features)
            results.append({
                "index":         i,
                "prediction":    res["prediction"],
                "probabilities": res["probabilities"],
                "confidence":    res["confidence"],
            })
        except Exception as exc:
            errors.append({"index": i, "error": str(exc)})

    return jsonify({
        "success": True,
        "total":   len(students),
        "results": results,
        "errors":  errors,
    }), 200
