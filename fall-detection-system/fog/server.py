# fog/server.py
from fastapi import FastAPI
from pydantic import BaseModel
import threading
import json
import time

import paho.mqtt.client as mqtt

from .alert_manager import AlertManager

app = FastAPI()

manager = AlertManager( # escalation policy (critiera)
    confidence_escalate=0.80,
    # multi_device_window_sec=8.0,
    # multi_device_count=2, // for future context when multi-camera arrangements are used
    escalation_cooldown_sec=15.0,
)

# mqtt config
import os
mqtt_broker = os.getenv("mqtt_broker", "127.0.0.1")
mqtt_port = 1883
mqtt_topic = "team17/edge/+/alert"


class AlertPayload(BaseModel): # defines the schema of oncoming alerts
    device_id: str
    event: str = "FALL_DETECTED"
    timestamp: float | None = None
    confidence: float = 0.0
    snapshot_path: str | None = None

# mqtt logic
def on_connect(client, userdata, flags, rc):
    print("[FOG] MQTT successfully connected rc=", rc)
    client.subscribe(mqtt_topic, qos=1)
    print("[FOG] MQTT successfully subscribed to", mqtt_topic)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception:
        print("[FOG] Received a Bad JSON on", msg.topic)
        return

    Stored = manager.ingest(payload, topic=msg.topic)
    if Stored:
        print(f"[FOG] Stored alert from {payload.get('device_id')} conf={payload.get('confidence')}")

def mqtt_thread():
    client = mqtt.Client(client_id="fog-node")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_broker, mqtt_port, keepalive=60)
    client.loop_forever()

@app.on_event("startup")
def startup():
    t = threading.Thread(target=mqtt_thread, daemon=True)
    t.start()
