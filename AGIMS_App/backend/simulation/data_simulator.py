"""
Synthetic GNSS data simulator — last-resort fallback.
Noise/drift magnitudes calibrated to Cleaned_GPS_Spoofing_Dataset.csv ranges.
"""
import numpy as np
import time
from typing import Dict
from config import FEATURE_RANGES, PRN_IDS


class GNSSDataSimulator:

    def __init__(self):
        self.start_time = time.time()
        self._base:  Dict[int, Dict[str, float]] = {}
        self._drift: Dict[int, Dict[str, float]] = {}
        self._init()

    def _init(self):
        for prn in PRN_IDS:
            self._base[prn]  = {f: float(np.random.uniform(*r)) for f, r in FEATURE_RANGES.items()}
            self._drift[prn] = {
                "DO":  float(np.random.uniform(-50,   50)),
                "PD":  float(np.random.uniform(-5000, 5000)),
                "CN0": float(np.random.uniform(-0.3,  0.3)),
                "TCD": float(np.random.uniform(-20,   20)),
            }

    def generate_sample(self, prn: int) -> Dict[str, float]:
        if prn not in self._base:
            # Unknown PRN — use first known as template
            prn = PRN_IDS[0]
        b = self._base[prn]
        d = self._drift[prn]
        t = time.time() - self.start_time

        DO  = b["DO"]  + d["DO"]  + 60  * np.sin(0.10 * t) + np.random.normal(0, 25)
        PD  = b["PD"]  + d["PD"]  + 400 * np.sin(0.05 * t) + np.random.normal(0, 800)
        CN0 = float(np.clip(b["CN0"] + d["CN0"] + np.random.normal(0, 0.3),
                            *FEATURE_RANGES["CN0"]))
        TCD = b["TCD"] + d["TCD"] + np.random.normal(0, 8)
        EC  = b["EC"]  + np.random.normal(0, 400)
        LC  = b["LC"]  + np.random.normal(0, 400)
        PC  = b["PC"]  + np.random.normal(0, 400)

        # Slowly evolve drifts
        d["DO"]  = float(np.clip(d["DO"]  + np.random.normal(0, 4),    -150,   150))
        d["PD"]  = float(np.clip(d["PD"]  + np.random.normal(0, 300),  -10000, 10000))
        d["CN0"] = float(np.clip(d["CN0"] + np.random.normal(0, 0.03), -0.8,   0.8))
        d["TCD"] = float(np.clip(d["TCD"] + np.random.normal(0, 1.5),  -40,    40))

        return {"DO": float(DO), "PD": float(PD), "CN0": float(CN0),
                "TCD": float(TCD), "EC": float(EC), "LC": float(LC), "PC": float(PC)}

    def get_timestamp(self) -> float:
        return time.time() - self.start_time

    def reset(self):
        self.start_time = time.time()
        self._init()
