# -*- coding: utf-8 -*-
"""
backend/app.py
--------------
Flask application factory (MongoDB version).
"""
import os
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

from backend.config               import Config
from backend.ml_model             import ModelStore
from backend.routes.predict       import predict_bp
from backend.routes.model_info    import model_bp
from backend.routes.alerts        import alerts_bp
from backend.routes.db_students   import db_bp
from backend.routes.attendance    import attendance_bp
from backend.routes.dashboard     import dashboard_bp
from backend.routes.notifications import notifications_bp


def create_app() -> Flask:
    # Serve static files from the compiled React build
    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'dist')
    app = Flask(__name__, static_folder=dist_dir)
    app.config.from_object(Config)

    # Allow all origins (tighten in production)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Load ML artefacts once at startup
    ModelStore.load()

    # Initialise MongoDB connection
    try:
        from database.db import init_db, get_db
        init_db()

        db = get_db()
        
        # Create indexes (idempotent — safe to run every startup)
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
        db["prediction_logs"].create_index("student_id")
        db["alert_records"].create_index("student_id")
        db["password_resets"].create_index("token", unique=True, sparse=True)
        
        # Ensure counters collection exists
        if db["counters"].count_documents({}) == 0:
            db["counters"].insert_many([
                {"_id": "student_marks_id", "seq": 0},
                {"_id": "attendance_id", "seq": 0},
                {"_id": "locked_assessments_id", "seq": 0},
                {"_id": "locked_attendance_id", "seq": 0},
                {"_id": "prediction_logs_id", "seq": 0},
                {"_id": "alert_records_id", "seq": 0},
            ])

        print("[DB] MongoDB indexes verified and ready.")
    except Exception as exc:
        print(f"[DB] WARNING: MongoDB connection failed. ({exc})")

    # Register blueprints
    app.register_blueprint(predict_bp)
    # app.register_blueprint(students_bp) - CSV route removed in favor of MongoDB db_bp
    app.register_blueprint(model_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(db_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(notifications_bp)

    # ── Root index & API Discovery ────────────────────────────────────────────
    @app.route("/api", methods=["GET"])
    def api_index():
        from database.db import _db
        return jsonify({
            "service": "Student Performance API",
            "version": "3.0.0",
            "db_available": _db is not None,
            "db_engine": "MongoDB Atlas",
            "endpoints": {
                "predict_single":        "POST /api/predict",
                "predict_batch":         "POST /api/predict/batch",
                "students_list":         "GET  /api/db/students",
                "students_get":          "GET  /api/db/students/<id>",
                "students_add":          "POST /api/db/students",
                "students_stats":        "GET  /api/db/students/stats",
                "students_search":       "GET  /api/db/students/search",
                "model_info":            "GET  /api/model/info",
                "model_evaluation":      "GET  /api/model/evaluation",
                "model_coefficients":    "GET  /api/model/coefficients",
                "model_retrain":         "POST /api/model/retrain",
                "health":               "GET  /api/health",
                "db_students_list":      "GET  /api/db/students",
                "db_students_get":       "GET  /api/db/students/<id>",
                "db_students_create":    "POST /api/db/students",
                "db_students_update":    "PUT  /api/db/students/<id>",
                "db_students_delete":    "DELETE /api/db/students/<id>",
                "db_students_history":   "GET  /api/db/students/<id>/history",
                "db_students_stats":     "GET  /api/db/students/stats",
                "db_predictions":        "GET  /api/db/predictions",
                "db_predictions_summary":"GET  /api/db/predictions/summary",
                "alerts_list":           "GET  /api/alerts",
                "alerts_summary":        "GET  /api/alerts/summary",
                "alerts_student":        "GET  /api/alerts/student/<id>",
                "alerts_resolve":        "POST /api/alerts/<id>/resolve",
                "dashboard":             "GET  /api/dashboard",
                "dashboard_scan":        "POST /api/dashboard/scan",
                "dashboard_at_risk":     "GET  /api/dashboard/at-risk",
                "notify_config":         "GET  /api/notifications/config",
                "notify_test":           "POST /api/notifications/test",
                "notify_send_alert":     "POST /api/notifications/send-alert",
            }
        }), 200

    # ── Serve React Frontend (SPA Fallback) ───────────────────────────────────
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

    # ── Global error handlers ─────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "error": "Route not found."}), 404
        return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "error": "Internal server error."}), 500

    return app
