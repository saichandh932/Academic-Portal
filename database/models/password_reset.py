# -*- coding: utf-8 -*-
"""
database/models/password_reset.py
---------------------------------
MongoDB model for managing password reset tokens.
"""
from database.db import get_db
import secrets
from datetime import datetime, timedelta


class PasswordResetModel:
    COL = "password_resets"

    @staticmethod
    def create_token(registration_number, role='Student'):
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=2)
        try:
            db = get_db()
            # Clean up existing tokens for this user
            db[PasswordResetModel.COL].delete_many({
                "registration_number": registration_number, "role": role
            })
            # Insert new token
            db[PasswordResetModel.COL].insert_one({
                "registration_number": registration_number,
                "role": role,
                "token": token,
                "expires_at": expires_at
            })
            return token
        except Exception as e:
            print(f"[DB] Error creating reset token: {e}")
            return None

    @staticmethod
    def verify_token(token):
        try:
            db = get_db()
            row = db[PasswordResetModel.COL].find_one({
                "token": token,
                "expires_at": {"$gt": datetime.now()}
            })
            if row:
                return row["registration_number"], row["role"]
        except Exception as e:
            print(f"[DB] Error verifying reset token: {e}")
        return None

    @staticmethod
    def delete_token(token):
        try:
            db = get_db()
            db[PasswordResetModel.COL].delete_one({"token": token})
            return True
        except Exception as e:
            print(f"[DB] Error deleting reset token: {e}")
            return False
