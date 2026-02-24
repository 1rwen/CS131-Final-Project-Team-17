# 1. Use NVIDIA's L4T image
FROM nvcr.io/nvidia/l4t-ml:r32.7.1-py3

WORKDIR /app

# 2. Add 'xvfb' to the list of things to install
RUN apt-get update && apt-get install -y \
    python3-opencv \
    libcanberra-gtk-module \
    libcanberra-gtk3-module \
    pkg-config \
    libv4l-dev \
    git \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# 3. CRITICAL: Force Python to look in the system folder for the Jetson's cv2 library
ENV PYTHONPATH=/usr/lib/python3.6/dist-packages:$PYTHONPATH

# Tell matplotlib to run in headless mode
ENV MPLBACKEND=Agg

# 4. Copy your project files
COPY ./edge /app/edge
COPY ./shared /app/shared

# 5. Install normal Python packages
RUN python3 -m pip install paho-mqtt requests fastapi uvicorn dataclasses matplotlib attrs absl-py protobuf

# 6. Install the custom MediaPipe wheel
RUN git clone --depth 1 https://github.com/anion0278/mediapipe-jetson.git && \
    mv mediapipe-jetson/dist/*.whl mediapipe-0.8.9-cp36-cp36m-linux_aarch64.whl && \
    python3 -m pip install mediapipe-0.8.9-cp36-cp36m-linux_aarch64.whl --no-deps && \
    rm -rf mediapipe-jetson mediapipe-0.8.9-cp36-cp36m-linux_aarch64.whl

# 7. Clear NVIDIA's default JupyterLab startup script
ENTRYPOINT []

# 8. Start your camera script INSIDE the fake virtual display!
CMD ["xvfb-run", "-a", "python3", "-u", "edge/pose_detection.py"]
