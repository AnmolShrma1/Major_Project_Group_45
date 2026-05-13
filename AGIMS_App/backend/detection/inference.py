"""
Inference engine — sliding-window inference over streaming GNSS data.
"""
import numpy as np
from typing import Dict, Optional
from detection.model_loader import ModelLoader
from detection.utils        import SlidingWindowBuffer
from config import WINDOW_SIZE, DETECTION_THRESHOLD


class InferenceEngine:

    def __init__(self):
        self.loader     = ModelLoader()
        self.buffer     = SlidingWindowBuffer(WINDOW_SIZE)
        self.latest:    Dict[int, float] = {}
        self.detections: Dict[int, int]  = {}

    def process_datapoint(self, prn: int, features: Dict[str, float]) -> Optional[float]:
        self.buffer.add_point(prn, features)
        if not self.buffer.is_ready(prn):
            return None
        risk = self.loader.predict(self.buffer.get_window(prn))
        self.latest[prn] = risk
        if risk >= DETECTION_THRESHOLD:
            self.detections[prn] = self.detections.get(prn, 0) + 1
        return risk

    def is_attack_detected(self, risk: float) -> bool:
        return risk >= DETECTION_THRESHOLD

    def get_latest(self, prn: int) -> float:
        return self.latest.get(prn, 0.0)

    def stats(self) -> Dict:
        return {"total": sum(self.detections.values()),
                "per_prn": dict(self.detections),
                "monitored": list(self.latest)}

    def reset(self):
        self.buffer.clear()
        self.latest.clear()
        self.detections.clear()

    def get_model_info(self) -> dict:
        return self.loader.get_model_info()
