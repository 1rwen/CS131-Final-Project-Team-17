import cv2
import mediapipe as mp
import paho.mqtt.client as mqtt
import json

# --- MQTT Setup ---
MQTT_BROKER = "localhost" # Or the IP of your MQTT container
MQTT_TOPIC = "home/alerts/fall"
client = mqtt.Client()
client.connect(MQTT_BROKER, 1883, 60)

# --- MediaPipe Setup ---
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5)

# --- Camera Setup (Jetson GStreamer) ---
pipeline = "v4l2src device=/dev/video0 ! video/x-raw, width=640, height=480 ! videoconvert ! appsink"
cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    if results.pose_landmarks:
        lm = results.pose_landmarks.landmark
        
        # 1. Get Head and Hip Y-coordinates
        head_y = lm[mp_pose.PoseLandmark.NOSE].y
        hip_y = (lm[mp_pose.PoseLandmark.LEFT_HIP].y + lm[mp_pose.PoseLandmark.RIGHT_HIP].y) / 2
        
        # 2. Heuristic: Fall if head is below hips
        if head_y > hip_y:
            print("⚠️ Fall Detected! Sending MQTT Alert...")
            payload = json.dumps({"status": "fall", "device": "jetson_nano_01"})
            client.publish(MQTT_TOPIC, payload)

    # Note: No cv2.imshow here if running headless/Docker
cap.release()
