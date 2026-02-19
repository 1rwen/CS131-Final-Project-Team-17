FROM nvcr.io/nvidia/l4t-ml:r32.7.1-py3

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3-opencv \
    libcanberra-gtk-module \
    libcanberra-gtk3-module \
    pkg-config \
    libv4l-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY ./edge /app/edge
COPY ./shared /app/shared

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install paho-mqtt requests fastapi uvicorn dataclasses matplotlib attrs absl-py protobuf && \
    git clone --depth 1 https://github.com/anion0278/mediapipe-jetson.git && \
    mv mediapipe-jetson/dist/*.whl mediapipe-0.8.9-cp36-cp36m-linux_aarch64.whl && \
    python3 -m pip install mediapipe-0.8.9-cp36-cp36m-linux_aarch64.whl --no-deps && \
    rm -rf mediapipe-jetson mediapipe-0.8.9-cp36-cp36m-linux_aarch64.whl

CMD ["python3", "edge/pose_detection.py"]
