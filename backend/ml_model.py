# -*- coding: utf-8 -*-
"""
backend/ml_model.py
-------------------
Singleton loader for the trained ML artefacts.
Loaded once at startup; shared across all request handlers.
"""
import joblib
import numpy as np
from backend.config import Config


class ModelStore:
    """Holds the loaded sklearn artefacts."""

    _model   = None
    _scaler  = None
    _encoder = None

    @classmethod
    def load(cls):
        """Load model, scaler, and label-encoder from disk."""
        cls._model   = joblib.load(Config.MODEL_PATH)
        cls._scaler  = joblib.load(Config.SCALER_PATH)
        cls._encoder = joblib.load(Config.ENCODER_PATH)
        print(f"[ModelStore] Loaded model   : {Config.MODEL_PATH}")
        print(f"[ModelStore] Loaded scaler  : {Config.SCALER_PATH}")
        print(f"[ModelStore] Loaded encoder : {Config.ENCODER_PATH}")

    # ── accessors ──────────────────────────────────────────────────────────────
    @classmethod
    def model(cls):
        if cls._model is None:
            raise RuntimeError("Model not loaded. Call ModelStore.load() first.")
        return cls._model

    @classmethod
    def scaler(cls):
        if cls._scaler is None:
            raise RuntimeError("Scaler not loaded. Call ModelStore.load() first.")
        return cls._scaler

    @classmethod
    def encoder(cls):
        if cls._encoder is None:
            raise RuntimeError("Encoder not loaded. Call ModelStore.load() first.")
        return cls._encoder

    # ── prediction helper ──────────────────────────────────────────────────────
    @classmethod
    def predict(cls, feature_dict: dict) -> dict:
        """
        Given a dict of {feature_name: value}, return:
          {
            "prediction": "High" | "Medium" | "Low",
            "probabilities": {"High": 0.xx, "Medium": 0.xx, "Low": 0.xx},
            "confidence": 0.xx
          }
        """
        features = [feature_dict[col] for col in Config.FEATURE_COLS]
        X = np.array(features, dtype=float).reshape(1, -1)
        X_scaled = cls.scaler().transform(X)

        pred_enc  = cls.model().predict(X_scaled)[0]
        proba     = cls.model().predict_proba(X_scaled)[0]
        class_names = cls.encoder().classes_

        prediction   = cls.encoder().inverse_transform([pred_enc])[0]
        proba_dict   = {cls_: round(float(p), 4)
                        for cls_, p in zip(class_names, proba)}
        confidence   = round(float(max(proba)), 4)

        return {
            "prediction":    prediction,
            "probabilities": proba_dict,
            "confidence":    confidence,
        }
