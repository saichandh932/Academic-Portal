# -*- coding: utf-8 -*-
"""
backend/routes/model_info.py
-----------------------------
Model metadata and management endpoints:

  GET  /api/model/info          - model metadata + feature list
  GET  /api/model/evaluation    - serve the evaluation PNG
  GET  /api/model/coefficients  - log-odds coefficients per class
  POST /api/model/retrain       - retrain the model on current CSV data
  GET  /api/health              - health-check
"""
import os
import base64
import subprocess
import sys

from flask import Blueprint, jsonify, send_file, request

from backend.config   import Config
from backend.ml_model import ModelStore

model_bp = Blueprint("model_info", __name__, url_prefix="/api")


# ── Health-check ───────────────────────────────────────────────────────────────
@model_bp.route("/health", methods=["GET"])
def health():
    """GET /api/health"""
    return jsonify({"success": True, "status": "ok"}), 200


# ── Model metadata ─────────────────────────────────────────────────────────────
@model_bp.route("/model/info", methods=["GET"])
def model_info():
    """GET /api/model/info"""
    m  = ModelStore.model()
    le = ModelStore.encoder()

    return jsonify({
        "success":      True,
        "model_type":   type(m).__name__,
        "solver":       m.solver,
        "max_iter":     m.max_iter,
        "C":            m.C,
        "classes":      list(le.classes_),
        "feature_cols": Config.FEATURE_COLS,
        "num_features": len(Config.FEATURE_COLS),
        "iterations_run": int(m.n_iter_[0]),
    }), 200


# ── Log-odds coefficients ──────────────────────────────────────────────────────
@model_bp.route("/model/coefficients", methods=["GET"])
def coefficients():
    """GET /api/model/coefficients"""
    m          = ModelStore.model()
    le         = ModelStore.encoder()
    class_names = le.classes_

    coef_dict = {
        cls_: {feat: round(float(val), 6)
               for feat, val in zip(Config.FEATURE_COLS, row)}
        for cls_, row in zip(class_names, m.coef_)
    }

    intercept_dict = {
        cls_: round(float(val), 6)
        for cls_, val in zip(class_names, m.intercept_)
    }

    return jsonify({
        "success":     True,
        "classes":     list(class_names),
        "features":    Config.FEATURE_COLS,
        "coefficients": coef_dict,
        "intercepts":   intercept_dict,
    }), 200


# ── Evaluation chart ───────────────────────────────────────────────────────────
@model_bp.route("/model/evaluation", methods=["GET"])
def evaluation_image():
    """
    GET /api/model/evaluation
    Returns the saved evaluation PNG.
    Query param ?format=base64 to get a JSON-wrapped base64 string.
    """
    if not os.path.exists(Config.EVAL_IMG):
        return jsonify({"success": False,
                        "error": "Evaluation image not found. Run model training first."}), 404

    if request.args.get("format", "").lower() == "base64":
        with open(Config.EVAL_IMG, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return jsonify({
            "success":    True,
            "image_b64":  b64,
            "media_type": "image/png",
        }), 200

    return send_file(Config.EVAL_IMG, mimetype="image/png")


# ── Retrain ────────────────────────────────────────────────────────────────────
@model_bp.route("/model/retrain", methods=["POST"])
def retrain():
    """
    POST /api/model/retrain
    Re-runs model/train.py against the current students.csv,
    then hot-reloads the artefacts into ModelStore.

    Returns the new accuracy metrics on success.
    """
    train_script = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "model", "train.py"
    )

    if not os.path.exists(train_script):
        return jsonify({"success": False,
                        "error": "train.py not found."}), 500

    result = subprocess.run(
        [sys.executable, train_script],
        capture_output=True, text=True,
        env={**os.environ, "PYTHONUTF8": "1"},
    )

    if result.returncode != 0:
        return jsonify({
            "success": False,
            "error":   "Training script failed.",
            "stdout":  result.stdout[-2000:],
            "stderr":  result.stderr[-2000:],
        }), 500

    # Hot-reload artefacts
    ModelStore.load()

    # Parse accuracy lines from stdout
    metrics = {}
    for line in result.stdout.splitlines():
        if "Training Accuracy" in line:
            metrics["train_accuracy"] = line.split(":")[-1].strip()
        elif "Test Accuracy" in line:
            metrics["test_accuracy"] = line.split(":")[-1].strip()
        elif "CV Accuracy" in line:
            metrics["cv_accuracy"] = line.split(":")[-1].strip()

    return jsonify({
        "success":  True,
        "message":  "Model retrained and reloaded successfully.",
        "metrics":  metrics,
        "log_tail": result.stdout[-1500:],
    }), 200
