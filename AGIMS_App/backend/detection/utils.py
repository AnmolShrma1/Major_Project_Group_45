"""
Sliding-window buffer and helper utilities for the detection layer.
"""
import numpy as np
from collections import deque
from typing import Dict, List, Optional


FEATURE_ORDER = ["DO", "PD", "CN0", "TCD", "EC", "LC", "PC"]


class SlidingWindowBuffer:
    """Per-PRN circular buffer that yields (window_size, 7) numpy arrays."""

    def __init__(self, window_size: int):
        self.window_size = window_size
        self._bufs: Dict[int, deque] = {}

    def add_point(self, prn: int, features: Dict[str, float]):
        if prn not in self._bufs:
            self._bufs[prn] = deque(maxlen=self.window_size)
        self._bufs[prn].append([features[f] for f in FEATURE_ORDER])

    def get_window(self, prn: int) -> Optional[np.ndarray]:
        if not self.is_ready(prn):
            return None
        return np.array(list(self._bufs[prn]), dtype=float)

    def is_ready(self, prn: int) -> bool:
        return prn in self._bufs and len(self._bufs[prn]) == self.window_size

    def clear(self):
        self._bufs.clear()


def calculate_trend(values: List[float], window: int = 5) -> float:
    if len(values) < window:
        return 0.0
    y = np.array(values[-window:])
    x = np.arange(len(y))
    return float(np.polyfit(x, y, 1)[0])
