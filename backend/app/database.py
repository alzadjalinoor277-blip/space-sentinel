"""
SQLite persistence for SpaceSentinel.

Kept intentionally lightweight: mission events and resolved anomaly history
are persisted so the Mission Logs page has continuity across backend
restarts. Live in-flight state (current telemetry window, active anomalies)
is held in memory by the simulation engine for performance and simplicity.
"""
import sqlite3
import json
import os
from contextlib import contextmanager
from typing import Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spacesentinel.db")


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mission_events (
                id TEXT PRIMARY KEY,
                timestamp REAL NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS anomaly_history (
                id TEXT PRIMARY KEY,
                timestamp REAL NOT NULL,
                data TEXT NOT NULL
            )
            """
        )
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def insert_event(event: dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO mission_events (id, timestamp, category, severity, message) "
            "VALUES (?, ?, ?, ?, ?)",
            (event["id"], event["timestamp"], event["category"], event["severity"], event["message"]),
        )
        conn.commit()


def list_events(limit: int = 200) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM mission_events ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def insert_anomaly_record(anomaly_id: str, timestamp: float, data: dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO anomaly_history (id, timestamp, data) VALUES (?, ?, ?)",
            (anomaly_id, timestamp, json.dumps(data)),
        )
        conn.commit()


def list_anomaly_history(limit: int = 200) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM anomaly_history ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [json.loads(r["data"]) for r in rows]


def clear_all() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM mission_events")
        conn.execute("DELETE FROM anomaly_history")
        conn.commit()
