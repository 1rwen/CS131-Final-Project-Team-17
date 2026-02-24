FROM python:3.10-slim

WORKDIR /app

COPY ./fog /app/fog
COPY ./shared /app/shared

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    paho-mqtt \
    requests \
    pydantic

CMD ["python", "-m", "fog.server"]
