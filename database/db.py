# -*- coding: utf-8 -*-
"""
database/db.py
--------------
MongoDB connection layer using PyMongo.
Provides get_db() to access the database and a DB() context manager
for backward compatibility with existing code patterns.
"""
import os
from pymongo import MongoClient
from backend.config import Config

_client: MongoClient | None = None
_db = None


def init_db() -> None:
    """
    Create the MongoDB connection.
    Called once from create_app() before the first request or lazily if needed.
    """
    global _client, _db
    if _db is not None:
        return

    try:
        uri = Config.MONGO_URI
        db_name = Config.DB_NAME
        
        # Check for placeholder or dangerous defaults in Vercel
        if "localhost" in uri and os.getenv("VERCEL") == "1":
            print("[DB] WARNING: MONGO_URI is set to localhost in Vercel environment.")

        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _db = _client[db_name]
        
        # Force a connection test
        _client.admin.command('ping')
        print(f"[DB] MongoDB connected -> {db_name}")
    except Exception as err:
        print(f"[DB] ERROR: Could not connect to MongoDB cluster. Check MONGO_URI. Details: {err}")
        _client = None
        _db = None


def get_db():
    """Return the pymongo Database object, initializing if necessary."""
    global _db
    if _db is None:
        init_db()
    if _db is None:
        raise RuntimeError(
            "MongoDB not initialised. Ensure 'MONGO_URI' is set in your environment variables. "
            "If on Vercel, check the Dashboard Settings."
        )
    return _db


def get_collection(name: str):
    """Return a specific collection from the database."""
    return get_db()[name]


def get_next_id(counter_name: str) -> int:
    """Auto-increment counter for collections that need sequential IDs."""
    db = get_db()
    result = db["counters"].find_one_and_update(
        {"_id": counter_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return result["seq"]


# ── Context-manager helper (backward compat) ─────────────────────────────────
class DB:
    """
    Usage (MongoDB style):
        with DB() as db:
            db.students.find(...)
            db.students.insert_one(...)

    No conn/cur, no commit needed — MongoDB auto-commits.
    """
    def __enter__(self):
        return get_db()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False  # re-raise any exception
