import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

cap = cv2.VideoCapture("v4l2src device=/dev/video0 ! video/x-raw, width=640, height=480 ! videoconvert ! appsink", cv2.CAP_GSTREAMER)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = pose.process(rgb)

    if result.pose_landmarks:
        mp.solutions.drawing_utils.draw_landmarks(
            frame,
            result.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

    cv2.imshow("Pose", frame)

    if cv2.waitKey(1) == 27: #esc key to exit
        break
