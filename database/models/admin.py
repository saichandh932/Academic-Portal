# -*- coding: utf-8 -*-
"""
database/models/admin.py
-------------------------
MongoDB model for Admin account persistence and verification.
"""
from database.db import get_db


class AdminModel:
    COL = "admins"

    @staticmethod
    def verify_credentials(username, password):
        try:
            db = get_db()
            row = db[AdminModel.COL].find_one(
                {"username": username, "password": password},
                {"assigned_subject": 1}
            )
            if row:
                return row["assigned_subject"]
        except Exception as e:
            print(f"[DB] Admin verification error: {e}")
            return None
        return None

    @staticmethod
    def bulk_create(admins_list):
        try:
            db = get_db()
            from pymongo import UpdateOne
            ops = [
                UpdateOne(
                    {"username": a["username"]},
                    {"$set": {
                        "username": a["username"],
                        "password": a["password"],
                        "assigned_subject": a["assigned_subject"]
                    }},
                    upsert=True
                ) for a in admins_list
            ]
            db[AdminModel.COL].bulk_write(ops)
            return True
        except Exception as e:
            print(f"[DB] Admin bulk create error: {e}")
            return False

    @staticmethod
    def update_password(username, new_password):
        try:
            db = get_db()
            result = db[AdminModel.COL].update_one(
                {"username": username},
                {"$set": {"password": new_password}}
            )
            return result.modified_count > 0 or result.matched_count > 0
        except Exception as e:
            print(f"[DB] Admin password update error: {e}")
            return False

    @staticmethod
    def get_email(username):
        return "admin@vignan.ac.in"
