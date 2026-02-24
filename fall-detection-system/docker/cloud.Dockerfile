FROM python:3.9-slim

WORKDIR /app

# Pinning specific versions to prevent Exit 132 (Illegal Instruction) on the Jetson Nano
RUN pip install --no-cache-dir \
    numpy==1.23.5 \
    pandas==1.5.3 \
    pyarrow==10.0.1 \
    streamlit==1.28.0 \
    requests

COPY cloud/ /app/cloud/

EXPOSE 8501

CMD ["streamlit", "run", "cloud/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
