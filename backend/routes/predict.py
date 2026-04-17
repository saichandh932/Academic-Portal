# -*- coding: utf-8 -*-
"""
backend/routes/predict.py
--------------------------
POST /api/predict        - predict single student performance
POST /api/predict/batch  - predict a list of students at once
"""
from flask import Blueprint, request, jsonify
from backend.ml_model import ModelStore
from backend.config   import Config

predict_bp = Blueprint("predict", __name__, url_prefix="/api")


def _validate_features(data: dict) -> tuple[dict | None, str | None]:
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
    if not (0 <= features["attendance"] <= 100):
        return None, "attendance must be between 0 and 100."
    if not (0 <= features["previous_score"] <= 100):
        return None, "previous_score must be between 0 and 100."
    if not (0 <= features["assignments"] <= 100):
        return None, "assignments must be between 0 and 100."
    if not (0 <= features["internal_marks"] <= 100):
        return None, "internal_marks must be between 0 and 100."
    if not (0 <= features["study_hours"] <= 24):
        return None, "study_hours must be between 0 and 24."

    return features, None


# ── Single prediction ──────────────────────────────────────────────────────────
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

    Response:
      {
        "success": true,
        "prediction": "High" | "Medium" | "Low",
        "probabilities": {"High": 0.xx, "Medium": 0.xx, "Low": 0.xx},
        "confidence": 0.xx,
        "input": { ...original fields... }
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

    # Silently log to DB and raise alerts (fails gracefully if DB is down)
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
        process_prediction(
            features      = features,
            prediction    = result["prediction"],
            confidence    = result["confidence"],
            prediction_id = pred_id,
        )
    except Exception:
        pass   # DB logging must never affect the API response

    return jsonify({
        "success":       True,
        "prediction":    result["prediction"],
        "probabilities": result["probabilities"],
        "confidence":    result["confidence"],
        "input":         features,
    }), 200


# ── Batch prediction ───────────────────────────────────────────────────────────
@predict_bp.route("/predict/batch", methods=["POST"])
def predict_batch():
    """
    Predict performance for multiple students in a single call.

    Request body (JSON):
      {
        "students": [
          { "study_hours": ..., "attendance": ..., ... },
          ...
        ]
      }

    Response:
      {
        "success": true,
        "total": N,
        "results": [
          { "index": 0, "prediction": "High", "probabilities": {...}, "confidence": 0.xx },
          ...
        ],
        "errors": [
          { "index": 1, "error": "..." },
          ...
        ]
      }
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
