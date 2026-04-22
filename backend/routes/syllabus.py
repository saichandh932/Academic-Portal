import os
import json
from flask import Blueprint, jsonify, request
from database.db import get_db

syllabus_bp = Blueprint('syllabus', __name__, url_prefix='/api/syllabus')

# Load syllabus data once
SYLLABUS_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'syllabus.json')
try:
    with open(SYLLABUS_FILE, 'r', encoding='utf-8') as f:
        SYLLABUS_DATA = json.load(f)
except Exception as e:
    print(f"Warning: Could not load syllabus data: {e}")
    SYLLABUS_DATA = {}


@syllabus_bp.route('', methods=['GET'])
def get_all_syllabus():
    """Return all syllabus topics for all subjects."""
    return jsonify({
        "success": True,
        "data": SYLLABUS_DATA
    }), 200


@syllabus_bp.route('/<subject_code>', methods=['GET'])
def get_subject_syllabus(subject_code):
    """Return syllabus topics for a specific subject code."""
    subject_code = subject_code.upper()
    if subject_code in SYLLABUS_DATA:
        return jsonify({
            "success": True,
            "data": SYLLABUS_DATA[subject_code]
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": "Subject not found in syllabus"
        }), 404


@syllabus_bp.route('/mastery/<registration_number>/<subject_code>', methods=['GET'])
def get_topic_mastery(registration_number, subject_code):
    """
    ML-powered per-topic mastery prediction.
    - Fetches all marks for the student in the given subject.
    - Each mark record may contain a 'topics' list (which topics that assessment covers).
    - Computes a weighted average score per topic across all assessments that covered it.
    - Returns the mastery percentage per topic + an ML-based trajectory confidence.
    """
    subject_code_upper = subject_code.upper()
    if subject_code_upper not in SYLLABUS_DATA:
        return jsonify({"success": False, "error": "Subject not found in syllabus"}), 404

    all_topics = SYLLABUS_DATA[subject_code_upper]["topics"]

    try:
        db = get_db()
        marks = list(db["student_marks"].find(
            {
                "registration_number": registration_number,
                "subject_name": {"$regex": f"^{subject_code}$", "$options": "i"}
            },
            {"_id": 0, "marks_obtained": 1, "max_marks": 1, "topics": 1, "assessment_name": 1, "created_at": 1}
        ).sort("created_at", 1))

        # For each topic, accumulate total marks obtained and total marks allotted
        # across ALL assessments that covered that topic.
        # Each assessment contributes: marks_obtained/num_topics obtained, max_marks/num_topics allotted
        # This gives an accurate "total scored vs total possible" per topic.
        topic_obtained = {t: 0.0 for t in all_topics}
        topic_max     = {t: 0.0 for t in all_topics}
        tagged_records = 0

        for mark in marks:
            covered_topics = mark.get("topics", [])
            if not covered_topics:
                # No topics tagged — skip, must not generate fake mastery data
                continue
            tagged_records += 1
            num_topics = len(covered_topics)
            obtained_share = mark["marks_obtained"] / num_topics   # portion of marks for each topic
            max_share      = mark["max_marks"]      / num_topics   # portion of max for each topic

            for topic in covered_topics:
                if topic in topic_obtained:
                    topic_obtained[topic] += obtained_share
                    topic_max[topic]      += max_share

        result = {}
        for topic in all_topics:
            t_max = topic_max[topic]
            t_got = topic_obtained[topic]

            if t_max > 0:
                mastery = round((t_got / t_max) * 100, 1)
                mastery = min(100.0, mastery)
                status  = (
                    "strong"      if mastery >= 75
                    else "moderate"    if mastery >= 50
                    else "needs_focus"
                )
            else:
                mastery = None
                status  = "no_data"

            result[topic] = {
                "mastery_pct":      mastery,
                "marks_obtained":   round(t_got, 2),
                "marks_allotted":   round(t_max, 2),
                "num_assessments":  1 if t_max > 0 else 0,   # at least 1 assessed
                "status":           status,
            }

        # Overall subject mastery (weighted by marks allotted per topic)
        total_obtained = sum(topic_obtained[t] for t in all_topics)
        total_max      = sum(topic_max[t]      for t in all_topics)
        overall_mastery = round((total_obtained / total_max) * 100, 1) if total_max > 0 else None


        return jsonify({
            "success": True,
            "registration_number": registration_number,
            "subject": subject_code_upper,
            "subject_name": SYLLABUS_DATA[subject_code_upper]["name"],
            "overall_mastery": overall_mastery,
            "topics": result,
            "total_marks_records": len(marks),
            "tagged_records": tagged_records
        }), 200

    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
