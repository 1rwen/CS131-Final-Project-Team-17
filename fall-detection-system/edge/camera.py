import cv2
import mediapipe as mp
import paho.mqtt.client as mqtt
import json
import time

# --- Configuration ---
# Use localhost if running directly on the Nano where Docker is hosted.
# If running on a separate machine, use the Jetson's IP address.
MQTT_BROKER = "localhost" 
MQTT_TOPIC = "fall/alerts" # Ensure your Fog node is subscribed to this topic
COOLDOWN_TIME = 5.0 # Wait 5 seconds before sending another alert

# --- MQTT Setup ---
client = mqtt.Client()
try:
    client.connect(MQTT_BROKER, 1883, 60)
    print("✅ Connected to MQTT Broker")
except Exception as e:
    print(f"❌ Failed to connect to MQTT: {e}")

# --- MediaPipe Setup ---
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# --- Camera Setup ---
pipeline = "v4l2src device=/dev/video0 ! video/x-raw, width=640, height=480 ! videoconvert ! appsink"
cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("❌ Camera not accessible. Check GStreamer pipeline.")
    exit()

print("🎥 Camera opened successfully. Monitoring for falls...")

last_alert_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert to RGB for MediaPipe
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = pose.process(rgb)

    if result.pose_landmarks:
        lm = result.pose_landmarks.landmark
        
        # 1. Extract Y-coordinates for Head and Hips
        head_y = lm[mp_pose.PoseLandmark.NOSE].y
        hip_y = (lm[mp_pose.PoseLandmark.LEFT_HIP].y + lm[mp_pose.PoseLandmark.RIGHT_HIP].y) / 2
        
        # 2. Heuristic Logic: Is the head below the hips?
        if head_y > hip_y:
            current_time = time.time()
            
            # 3. Cooldown check to prevent spamming
            if (current_time - last_alert_time) > COOLDOWN_TIME:
                print("⚠️ FALL DETECTED! Sending alert to Fog node...")
                
                # Create payload matching what your Fog/Cloud expects
                payload = {
                    "device_id": "jetson_nano_cam_1",
                    "status": "critical",
                    "timestamp": int(current_time)
                }
                
                # Publish to MQTT Broker
                client.publish(MQTT_TOPIC, json.dumps(payload))
                last_alert_time = current_time

    # Optional: Show the video feed on the Jetson desktop for debugging
    # Comment these two lines out if running completely headless
    cv2.imshow("Edge Fall Detection", frame)
    if cv2.waitKey(1) == 27: # ESC key to exit
        break

cap.release()
cv2.destroyAllWindows()
