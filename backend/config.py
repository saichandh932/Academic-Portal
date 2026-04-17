# -*- coding: utf-8 -*-
"""
backend/config.py
-----------------
Central configuration for the Flask app.
"""
import os
from dotenv import load_dotenv

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Load environment variables from the project root .env file
load_dotenv(os.path.join(BASE_DIR, "..", ".env"))

MODEL_DIR = os.path.join(BASE_DIR, "model")
DATA_DIR  = os.path.join(BASE_DIR, "data")

class Config:
    # Flask
    SECRET_KEY  = os.getenv("SECRET_KEY", "student-perf-secret-2024")
    DEBUG       = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    HOST        = os.getenv("HOST", "0.0.0.0")
    PORT        = int(os.getenv("PORT", 5000))
    # Admin Login (Mocked via Env for prototype phase)
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password")

    # Files
    MODEL_PATH   = os.path.join(MODEL_DIR, "logistic_model.pkl")
    SCALER_PATH  = os.path.join(MODEL_DIR, "scaler.pkl")
    ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")
    DATA_PATH    = os.path.join(DATA_DIR,  "students.csv")
    EVAL_IMG     = os.path.join(MODEL_DIR, "evaluation.png")

    # ML
    FEATURE_COLS = [
        "study_hours",
        "attendance",
        "previous_score",
        "assignments",
        "internal_marks",
    ]

    # MongoDB
    MONGO_URI    = os.getenv("MONGO_URI", "mongodb://localhost:27017/student_performance_db")
    DB_NAME      = os.getenv("DB_NAME",  "student_performance_db")

    # Alert thresholds
    ALERT_LOW_ATTENDANCE    = float(os.getenv("ALERT_LOW_ATTENDANCE",    40.0))
    ALERT_LOW_STUDY_HOURS   = float(os.getenv("ALERT_LOW_STUDY_HOURS",    2.0))
    ALERT_LOW_PREV_SCORE    = float(os.getenv("ALERT_LOW_PREV_SCORE",    30.0))

    # SMTP / Email
    SMTP_HOST        = os.getenv("SMTP_HOST",        "smtp.gmail.com")
    SMTP_PORT        = int(os.getenv("SMTP_PORT",    587))
    SMTP_USE_TLS     = os.getenv("SMTP_USE_TLS",     "true").lower() == "true"
    SMTP_USER        = os.getenv("SMTP_USER",        "")
    SMTP_PASSWORD    = os.getenv("SMTP_PASSWORD",    "")
    SMTP_FROM_NAME   = os.getenv("SMTP_FROM_NAME",   "Vignan Academic Portal")
    ALERT_EMAIL_TO   = os.getenv("ALERT_EMAIL_TO",   "")
    EMAIL_ENABLED    = os.getenv("EMAIL_ENABLED",    "true").lower() == "true"
    FRONTEND_URL     = os.getenv("FRONTEND_URL",     "http://localhost:5173")
