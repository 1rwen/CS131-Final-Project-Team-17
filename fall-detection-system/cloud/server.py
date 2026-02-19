from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import json
import time
from typing import List

app = FastAPI()

DB_PATH = "cloud.db"


# -------------------
# DATABASE SETUP
# -------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS escalations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp REAL,
        reason TEXT,
        involved_devices TEXT,
        max_confidence REAL
    )
    """)

    conn.commit()
    conn.close()


init_db()


# -------------------
# DATA MODEL
# -------------------
class EscalationPayload(BaseModel):
    timestamp: float
    reason: str
    involved_devices: List[str]
    max_confidence: float


# -------------------
# API ENDPOINTS
# -------------------
@app.post("/event")
def receive_event(event: EscalationPayload):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO escalations (timestamp, reason, involved_devices, max_confidence)
    VALUES (?, ?, ?, ?)
    """, (
        event.timestamp,
        event.reason,
        json.dumps(event.involved_devices),
        event.max_confidence
    ))

    conn.commit()
    conn.close()

    return {"status": "stored"}


@app.get("/history")
def get_history():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    SELECT timestamp, reason, involved_devices, max_confidence
    FROM escalations
    ORDER BY timestamp DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "timestamp": r[0],
            "reason": r[1],
            "involved_devices": json.loads(r[2]),
            "max_confidence": r[3],
        }
        for r in rows
    ]
