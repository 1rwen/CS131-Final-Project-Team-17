from fastapi import FastAPI

app = FastAPI()

alerts = []

@app.post("/alert")
def receive_alert(alert: str):
    alerts.append(alert)
    return {"status": "received"}
