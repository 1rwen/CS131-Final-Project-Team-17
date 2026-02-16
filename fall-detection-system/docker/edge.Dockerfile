FROM python:3.10-slim

WORKDIR /app

COPY ../edge /app/edge
COPY ../shared /app/shared

RUN pip install --no-cache-dir \
    opencv-python \
    mediapipe \
    scikit-learn \
    paho-mqtt

CMD ["python", "edge/camera.py"]
