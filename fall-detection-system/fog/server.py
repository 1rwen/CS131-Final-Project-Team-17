# fog/server.py
from fastapi import FastAPI
from pydantic import BaseModel
import threading
import json
import time

import paho.mqtt.client as mqtt

from .alert_manager import AlertManager

app = FastAPI()
manager = AlertManager(
    confidence_escalate=0.80,
    multi_device_window_sec=8.0,
    multi_device_count=2,
    escalation_cooldown_sec=15.0,
)

# ---- MQTT Config ----
import os
MQTT_BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
MQTT_PORT = 1883
MQTT_TOPIC = "team17/edge/+/alert"


class AlertPayload(BaseModel):
    device_id: str
    event: str = "FALL_DETECTED"
    timestamp: float | None = None
    confidence: float = 0.0
    snapshot_path: str | None = None


# ---- REST fallback (still useful for testing) ----
@app.post("/alert")
def receive_alert(alert: AlertPayload):
    payload = alert.model_dump()
    if payload["timestamp"] is None:
        payload["timestamp"] = time.time()
    stored = manager.ingest(payload, topic="rest:/alert")
    return {"status": "received", "stored": stored is not None}


@app.get("/alerts")
def list_alerts(limit: int = 50):
    return manager.get_alerts(limit=limit)


@app.get("/escalations")
def list_escalations(limit: int = 50):
    return manager.get_escalations(limit=limit)


@app.get("/health")
def health():
    return {"ok": True}


# ---- MQTT loop ----
def on_connect(client, userdata, flags, rc):
    print("[FOG] MQTT connected rc=", rc)
    client.subscribe(MQTT_TOPIC, qos=1)
    print("[FOG] Subscribed to", MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception:
        print("[FOG] Bad JSON on", msg.topic)
        return

    stored = manager.ingest(payload, topic=msg.topic)
    if stored:
        # optional log for demo visibility
        print(f"[FOG] Stored alert from {payload.get('device_id')} conf={payload.get('confidence')}")

def mqtt_thread():
    client = mqtt.Client(client_id="fog-node")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_forever()

@app.on_event("startup")
def startup():
    t = threading.Thread(target=mqtt_thread, daemon=True)
    t.start()
