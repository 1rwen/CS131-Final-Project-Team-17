FROM python:3.10-slim

WORKDIR /app

COPY ../fog /app/fog

RUN pip install fastapi uvicorn paho-mqtt

CMD ["uvicorn", "fog.server:app", "--host", "0.0.0.0", "--port", "8000"]