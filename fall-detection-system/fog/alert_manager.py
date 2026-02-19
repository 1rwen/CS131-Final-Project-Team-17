# fog/alert_manager.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
import time
import threading
import requests 

@dataclass
class Alert:
    alert_id: str
    device_id: str
    event: str
    timestamp: float
    confidence: float
    topic: str
    raw: Dict[str, Any]

@dataclass
class Escalation:
    escalation_id: str
    timestamp: float
    reason: str
    involved_devices: List[str] # might not be needed due to only using one webcam
    max_confidence: float
    related_alert_ids: List[str]

class AlertManager:
    def __init__(
        self,
        confidence_escalate: float = 0.80,
        # multi_device_window_sec: float = 8.0, // reconsider multi due to only having one camera
        # multi_device_count: int = 2,
        escalation_cooldown_sec: float = 15.0,
        max_alerts: int = 500,
        cloud_url: str = "http://localhost:9000/event", 
    ):
        self.confidence_escalate = confidence_escalate
        # self.multi_device_window_sec = multi_device_window_sec
        # self.multi_device_count = multi_device_count
        self.escalation_cooldown_sec = escalation_cooldown_sec
        self.max_alerts = max_alerts
        self.cloud_url = cloud_url

        self._lock = threading.Lock()
        self._alerts: List[Alert] = []
        self._escalations: List[Escalation] = []
        self._last_escalation_ts: float = 0.0
        self._dedupe: Dict[Tuple[str, str, int], float] = {}

    def _make_alert_id(self, device_id: str, ts: float, event: str) -> str:
        return f"{device_id}:{event}:{int(ts*1000)}"

    def _make_escalation_id(self) -> str:
        return f"esc:{int(time.time()*1000)}"

    def forward_to_cloud(self, esc: Escalation) -> None:
        pass #bypass bc cloud streamlit pulls data

    def _dedupe_key(self, device_id: str, event: str, ts: float) -> Tuple[str, str, int]:
        return (device_id, event, int(ts))

    def ingest(self, payload: Dict[str, Any], topic: str = "") -> Optional[Alert]:
        try:
            device_id = str(payload.get("device_id", "unknown"))
            event = str(payload.get("event", "UNKNOWN"))
            ts = float(payload.get("timestamp", time.time()))
            conf = float(payload.get("confidence", 0.0))
        except Exception:
            return None

        key = self._dedupe_key(device_id, event, ts)

        with self._lock:
            now = time.time()

            if len(self._dedupe) > 2000:
                cutoff = now - 60
                self._dedupe = {k: v for k, v in self._dedupe.items() if v >= cutoff}

            if key in self._dedupe and (now - self._dedupe[key]) < 10:
                return None
            self._dedupe[key] = now

            alert = Alert(
                alert_id=self._make_alert_id(device_id, ts, event),
                device_id=device_id,
                event=event,
                timestamp=ts,
                confidence=conf,
                topic=topic,
                raw=payload,
            )

            self._alerts.append(alert)
            if len(self._alerts) > self.max_alerts:
                self._alerts = self._alerts[-self.max_alerts :]

            esc = self._maybe_escalate(alert)
            if esc:
                self._escalations.append(esc)
                if len(self._escalations) > 200:
                    self._escalations = self._escalations[-200:]

                self.forward_to_cloud(esc)

            return alert

    def _maybe_escalate(self, new_alert: Alert) -> Optional[Escalation]:
        now = time.time()
        if now - self._last_escalation_ts < self.escalation_cooldown_sec:
            return None

        if new_alert.confidence >= self.confidence_escalate:
            self._last_escalation_ts = now
            return Escalation(
                escalation_id=self._make_escalation_id(),
                timestamp=now,
                reason=f"confidence>={self.confidence_escalate}",
                involved_devices=[new_alert.device_id],
                max_confidence=new_alert.confidence,
                related_alert_ids=[new_alert.alert_id],
            )

        return None


    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return [asdict(a) for a in self._alerts[-limit:]][::-1]

    def get_escalations(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return [asdict(e) for e in self._escalations[-limit:]][::-1]
