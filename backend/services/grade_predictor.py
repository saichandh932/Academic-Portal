# -*- coding: utf-8 -*-
"""
backend/services/grade_predictor.py
-------------------------------------
Semester-end grade prediction using Ridge Regression.

Predicts:
  - expected_percentage : float (0–100)
  - grade_letter        : S | A | B | C | D | F  (Vignan grading scale)
  - grade_points        : float (10-scale GPA points)
  - risk_score          : int 0–100 (0 = safe, 100 = critical)
  - risk_level          : "safe" | "moderate" | "high" | "critical"

The regression model is trained on the same students.csv that the classifier uses.
If the model file doesn't exist yet, it trains on-the-fly and caches it.
"""
from __future__ import annotations
import os
import joblib
import numpy as np
import pandas as pd

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR  = os.path.join(BASE_DIR, "model")
DATA_PATH  = os.path.join(BASE_DIR, "data", "students.csv")
REG_PATH   = os.path.join(MODEL_DIR, "grade_regressor.pkl")
REG_SC_PATH= os.path.join(MODEL_DIR, "grade_regressor_scaler.pkl")

FEATURE_COLS = ["study_hours", "attendance", "previous_score", "assignments", "internal_marks"]

# ── Vignan Grading Scale ──────────────────────────────────────────────────────
GRADE_SCALE = [
    (90, "S", 10.0),
    (80, "A", 9.0),
    (70, "B", 8.0),
    (60, "C", 7.0),
    (50, "D", 6.0),
    (40, "E", 5.0),
    (0,  "F", 0.0),
]


def _pct_to_grade(pct: float) -> tuple[str, float]:
    for threshold, letter, points in GRADE_SCALE:
        if pct >= threshold:
            return letter, points
    return "F", 0.0


def _compute_risk_score(features: dict, predicted_pct: float) -> int:
    """
    Composite at-risk score (0 = completely safe, 100 = critical).
    Weights:
      - Low predicted_pct     : 40%
      - Low attendance         : 30%
      - Low study_hours        : 15%
      - Low internal_marks     : 15%
    """
    # Predicted percentage component (inverted)
    pct_risk   = max(0, min(100, 100 - predicted_pct))          # 0→safe, 100→fail

    # Attendance risk (below 75 is danger)
    att        = float(features.get("attendance", 75))
    att_risk   = max(0, min(100, (75 - att) * (100 / 75))) if att < 75 else 0

    # Study hours risk (below 4 is concern)
    sh         = float(features.get("study_hours", 4))
    sh_risk    = max(0, min(100, (4 - sh) * (100 / 4))) if sh < 4 else 0

    # Internal marks risk (below 60 is concern)
    im         = float(features.get("internal_marks", 60))
    im_risk    = max(0, min(100, (60 - im) * (100 / 60))) if im < 60 else 0

    composite  = (pct_risk * 0.40) + (att_risk * 0.30) + (sh_risk * 0.15) + (im_risk * 0.15)
    return int(round(composite))


def _risk_level(score: int) -> str:
    if score >= 70: return "critical"
    if score >= 45: return "high"
    if score >= 20: return "moderate"
    return "safe"


def _risk_color(level: str) -> str:
    return {"safe": "#22c55e", "moderate": "#f59e0b", "high": "#f97316", "critical": "#ef4444"}.get(level, "#94a3b8")


def _ensure_model():
    """Load or train the Ridge regression model."""
    if os.path.exists(REG_PATH) and os.path.exists(REG_SC_PATH):
        return joblib.load(REG_PATH), joblib.load(REG_SC_PATH)

    # Train fresh
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler

    df = pd.read_csv(DATA_PATH).dropna()

    # Build a synthetic target: map categorical performance to numeric
    perf_map = {"High": 85.0, "Medium": 60.0, "Low": 35.0}
    if "expected_score" in df.columns:
        y = df["expected_score"].values
    else:
        # Derive from features — weighted average as proxy for expected semester score
        df["_target"] = (
            df["previous_score"]  * 0.30 +
            df["internal_marks"]  * 0.35 +
            df["assignments"]     * 0.20 +
            df["attendance"]      * 0.10 +
            df["study_hours"].clip(0, 10) * 0.5
        )
        y = df["_target"].values

    X  = df[FEATURE_COLS].values
    sc = StandardScaler()
    Xs = sc.fit_transform(X)

    model = Ridge(alpha=1.0)
    model.fit(Xs, y)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, REG_PATH)
    joblib.dump(sc, REG_SC_PATH)
    return model, sc


def predict_grade(features: dict) -> dict:
    """
    Given a feature dict, returns grade prediction + risk score.

    Parameters
    ----------
    features : dict with keys matching FEATURE_COLS

    Returns
    -------
    dict:
        expected_percentage, grade_letter, grade_points,
        risk_score (0-100), risk_level, risk_color,
        grade_scale (full table for UI rendering)
    """
    model, scaler = _ensure_model()

    X_raw    = np.array([features.get(c, 0) for c in FEATURE_COLS], dtype=float)
    X_scaled = scaler.transform(X_raw.reshape(1, -1))
    raw_pred = float(model.predict(X_scaled)[0])

    # Clamp to 0–100
    expected_pct = round(max(0.0, min(100.0, raw_pred)), 1)
    letter, pts  = _pct_to_grade(expected_pct)

    risk = _compute_risk_score(features, expected_pct)
    level = _risk_level(risk)

    # Grade scale table for UI (show where student sits)
    grade_table = [
        {
            "range": f"≥ {t}%",
            "letter": l,
            "points": p,
            "is_predicted": letter == l
        }
        for t, l, p in GRADE_SCALE
    ]

    return {
        "expected_percentage": expected_pct,
        "grade_letter":        letter,
        "grade_points":        pts,
        "risk_score":          risk,
        "risk_level":          level,
        "risk_color":          _risk_color(level),
        "grade_table":         grade_table,
        "features_used":       {k: round(float(features.get(k, 0)), 2) for k in FEATURE_COLS},
    }
