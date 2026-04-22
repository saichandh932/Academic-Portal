# -*- coding: utf-8 -*-
"""
backend/services/explainer.py
------------------------------
Lightweight prediction explainability using Logistic Regression coefficients.

No external SHAP library needed — we use the model's own log-odds
coefficients to rank which features pushed the prediction toward each class,
and generate human-readable insight messages for students and admins.
"""
from __future__ import annotations
import numpy as np
from backend.ml_model import ModelStore
from backend.config import Config


# ── Thresholds for generating recommendation messages ─────────────────────────
_THRESHOLDS = {
    "attendance": {
        "critical": 60.0,
        "warning":  75.0,
        "target":   85.0,
    },
    "study_hours": {
        "critical": 2.0,
        "warning":  4.0,
        "target":   6.0,
    },
    "internal_marks": {
        "critical": 40.0,
        "warning":  60.0,
        "target":   75.0,
    },
    "assignments": {
        "critical": 40.0,
        "warning":  60.0,
        "target":   75.0,
    },
    "previous_score": {
        "critical": 35.0,
        "warning":  55.0,
        "target":   70.0,
    },
}

_FEATURE_LABELS = {
    "attendance":     "Attendance",
    "study_hours":    "Study Hours",
    "internal_marks": "Internal Marks",
    "assignments":    "Assignments",
    "previous_score": "Previous Score",
}

_MESSAGES = {
    "attendance": {
        "critical": "⚠️ Attendance is critically low ({val:.0f}%). Aim for at least {target:.0f}%.",
        "warning":  "📋 Attendance ({val:.0f}%) is below the 75% requirement. Attend more regularly.",
        "good":     "✅ Attendance ({val:.0f}%) is strong. Keep it up!",
    },
    "study_hours": {
        "critical": "⚠️ Study hours ({val:.1f} hrs/day) are very low. Target at least {target:.0f} hrs/day.",
        "warning":  "📚 Study hours ({val:.1f} hrs/day) could be improved. Aim for {target:.0f}+ hrs/day.",
        "good":     "✅ Study hours ({val:.1f} hrs/day) look good!",
    },
    "internal_marks": {
        "critical": "⚠️ Internal exam scores ({val:.1f}%) are very low. Seek extra help immediately.",
        "warning":  "📝 Internal marks ({val:.1f}%) are average. Improve quiz/test performance.",
        "good":     "✅ Internal marks ({val:.1f}%) are solid.",
    },
    "assignments": {
        "critical": "⚠️ Assignment scores ({val:.1f}%) are failing. Complete all pending assignments.",
        "warning":  "📌 Assignment scores ({val:.1f}%) need improvement. Submit all pending work.",
        "good":     "✅ Assignment completion ({val:.1f}%) is good.",
    },
    "previous_score": {
        "critical": "📊 Previous semester score ({val:.1f}%) was low — this semester is a chance to recover.",
        "warning":  "📊 Previous score ({val:.1f}%) was average. Use this semester to improve.",
        "good":     "✅ Strong previous score ({val:.1f}%) — maintain your momentum.",
    },
}


def _get_level(feature: str, value: float) -> str:
    t = _THRESHOLDS.get(feature)
    if not t:
        return "good"
    if value < t["critical"]:
        return "critical"
    if value < t["warning"]:
        return "warning"
    return "good"


def explain_prediction(features: dict, prediction: str, probabilities: dict) -> dict:
    """
    Generates a human-readable explanation for an ML prediction.

    Parameters
    ----------
    features     : dict of {feature_name: float}
    prediction   : "High" | "Medium" | "Low"
    probabilities: dict of {class: probability}

    Returns
    -------
    dict with keys:
        - summary      : one-line verdict
        - factors      : list of {feature, label, value, impact, level, message}
        - top_weakness : the most impactful negative factor
        - top_strength : the most impactful positive factor
        - recommendations : list of actionable strings
    """
    m          = ModelStore.model()
    le         = ModelStore.encoder()
    scaler     = ModelStore.scaler()
    cols       = Config.FEATURE_COLS

    # ── Compute signed contribution per feature for the predicted class ───────
    pred_class_idx = list(le.classes_).index(prediction)
    coefs          = m.coef_[pred_class_idx]   # shape: (n_features,)

    X_raw    = np.array([features[c] for c in cols], dtype=float)
    X_scaled = scaler.transform(X_raw.reshape(1, -1))[0]

    # Contribution = coef * scaled_value  (sign tells direction)
    contributions = coefs * X_scaled   # higher = pushed TOWARD predicted class

    factors = []
    for i, col in enumerate(cols):
        raw_val   = float(features[col])
        contrib   = float(contributions[i])
        level     = _get_level(col, raw_val)

        # Impact: for "Low" prediction, positive contribution = bad; for "High" = good
        if prediction == "High":
            impact = "positive" if contrib > 0 else "negative"
        elif prediction == "Low":
            impact = "negative" if contrib > 0 else "positive"
        else:  # Medium
            impact = "neutral" if abs(contrib) < 0.1 else ("positive" if contrib > 0 else "negative")

        t = _THRESHOLDS.get(col, {})
        msg_tmpl = _MESSAGES.get(col, {}).get(level, "")
        message  = msg_tmpl.format(val=raw_val, target=t.get("target", raw_val)) if msg_tmpl else ""

        factors.append({
            "feature":     col,
            "label":       _FEATURE_LABELS.get(col, col),
            "value":       round(raw_val, 2),
            "contribution":round(contrib, 4),
            "impact":      impact,
            "level":       level,
            "message":     message,
        })

    # Sort by absolute contribution (most impactful first)
    factors.sort(key=lambda f: abs(f["contribution"]), reverse=True)

    # ── Summary line ──────────────────────────────────────────────────────────
    conf_pct  = round(probabilities.get(prediction, 0) * 100, 1)
    emoji_map = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
    emoji     = emoji_map.get(prediction, "")
    summary   = (
        f"{emoji} Predicted performance: {prediction} "
        f"(confidence: {conf_pct}%)"
    )

    # ── Top weakness & strength ───────────────────────────────────────────────
    negatives = [f for f in factors if f["impact"] == "negative"]
    positives = [f for f in factors if f["impact"] == "positive"]

    top_weakness = negatives[0]["label"] if negatives else None
    top_strength = positives[0]["label"] if positives else None

    # ── Recommendations ───────────────────────────────────────────────────────
    recommendations = []

    att_val = float(features.get("attendance", 100))
    if att_val < 75:
        shortfall = 75 - att_val
        recommendations.append(
            f"Attend at least {shortfall:.0f}% more classes to reach the 75% minimum threshold."
        )

    sh_val = float(features.get("study_hours", 6))
    if sh_val < 4:
        recommendations.append(
            f"Increase daily study time from {sh_val:.1f} to at least 4 hours — "
            "study hours have the strongest impact on outcomes."
        )

    im_val = float(features.get("internal_marks", 60))
    if im_val < 60:
        recommendations.append(
            f"Internal exam scores ({im_val:.0f}%) are low. Practice previous papers "
            "and seek faculty help before the next assessment."
        )

    asgn_val = float(features.get("assignments", 60))
    if asgn_val < 60:
        recommendations.append(
            f"Complete pending assignments. Current score: {asgn_val:.0f}%."
        )

    if not recommendations:
        recommendations.append(
            "You are on track! Maintain your current study habits and attendance."
        )

    return {
        "summary":         summary,
        "prediction":      prediction,
        "confidence_pct":  conf_pct,
        "factors":         factors,
        "top_weakness":    top_weakness,
        "top_strength":    top_strength,
        "recommendations": recommendations,
    }
