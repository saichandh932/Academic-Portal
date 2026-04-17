# -*- coding: utf-8 -*-
"""
database/db.py
--------------
MongoDB connection layer using PyMongo.
Provides get_db() to access the database and a DB() context manager
for backward compatibility with existing code patterns.
"""
from pymongo import MongoClient
from backend.config import Config

_client: MongoClient | None = None
_db = None


def init_db() -> None:
    """
    Create the MongoDB connection.
    Called once from create_app() before the first request.
    """
    global _client, _db
    try:
        _client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
        _db = _client[Config.DB_NAME]
        # Force a connection test
        _client.admin.command('ping')
        print(f"[DB] MongoDB connected -> {Config.DB_NAME}")
    except Exception as err:
        print(f"[DB] ERROR: Could not connect to MongoDB. {err}")
        _client = None
        _db = None


def get_db():
    """Return the pymongo Database object."""
    if _db is None:
        raise RuntimeError("MongoDB not initialised. Call init_db() first.")
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
