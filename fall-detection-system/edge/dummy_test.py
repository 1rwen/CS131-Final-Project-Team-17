import time
import json
import paho.mqtt.client as mqtt

BROKER_ADDRESS = "127.0.0.1"
DEVICE_ID = "nano_01"
TOPIC = f"team17/edge/{DEVICE_ID}/alert"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Edge Device: Successfully connected to MQTT Broker!", flush=True)
    else:
        print(f"Edge Device: Failed to connect, return code {rc}", flush=True)

client = mqtt.Client(client_id=f"edge_{DEVICE_ID}")
client.on_connect = on_connect

print(f"Attempting to connect to broker at {BROKER_ADDRESS}...", flush=True)
client.connect(BROKER_ADDRESS, 1883, 60)
client.loop_start()

try:
    while True:
        payload = {
            "device_id": DEVICE_ID,
            "event": "FALL_DETECTED",
            "timestamp": time.time(),
            "confidence": 0.99,
            "snapshot_path": None 
        }
        
        print(f"Edge: Sending payload to {TOPIC} -> {payload}", flush=True)
        client.publish(TOPIC, json.dumps(payload), qos=1)
        
        time.sleep(5)

except KeyboardInterrupt:
    print("\nStopping dummy test...", flush=True)
    client.loop_stop()
    client.disconnect()
