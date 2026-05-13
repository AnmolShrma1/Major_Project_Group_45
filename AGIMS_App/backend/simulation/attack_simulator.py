"""
GNSS Spoofing Attack Simulator.
Injects simplistic / intermediate / sophisticated attack patterns.
All magnitudes calibrated to Cleaned_GPS_Spoofing_Dataset.csv feature scales.
"""
import numpy as np
import time
from typing import Dict, List, Optional
from config import ATTACK_PARAMS


class AttackSimulator:

    def __init__(self):
        self.active        = False
        self.attack_type   = "none"
        self.affected_prns: List[int] = []
        self.intensity     = 1.0
        self._start_time   = 0.0
        self._state:       Dict[int, Dict] = {}

    # ── Lifecycle ──────────────────────────────────────────────────────────────
    def start_attack(self, attack_type: str, prns: Optional[List[int]] = None,
                     intensity: float = 1.0):
        self.active        = True
        self.attack_type   = attack_type
        self.affected_prns = prns or []
        self.intensity     = intensity
        self._start_time   = time.time()
        for p in self.affected_prns:
            self._state[p] = {"phase": 0.0, "drift": 0.0, "smooth": 0.0}

    def stop_attack(self):
        self.active        = False
        self.attack_type   = "none"
        self.affected_prns = []
        self._state.clear()

    # ── Dispatch ───────────────────────────────────────────────────────────────
    def apply_attack(self, prn: int, features: Dict[str, float]) -> Dict[str, float]:
        if not self.active or prn not in self.affected_prns:
            return features
        dispatch = {
            "simplistic":    self._simplistic,
            "intermediate":  self._intermediate,
            "sophisticated": self._sophisticated,
        }
        fn = dispatch.get(self.attack_type)
        return fn(prn, features) if fn else features

    # ── Attack modes ───────────────────────────────────────────────────────────
    def _simplistic(self, prn: int, f: Dict[str, float]) -> Dict[str, float]:
        """Sudden large jumps — easy to detect."""
        p  = ATTACK_PARAMS["simplistic"]
        iv = self.intensity
        f["CN0"] += p["CN0_spike"] * iv
        f["DO"]  += p["DO_jump"]  * iv * np.random.choice([-1, 1])
        f["TCD"] += p["TCD_jump"] * iv * np.random.choice([-1, 1])
        f["EC"]  += np.random.normal(0, 8000 * iv)
        f["LC"]  += np.random.normal(0, 8000 * iv)
        f["PC"]  += np.random.normal(0, 8000 * iv)
        return f

    def _intermediate(self, prn: int, f: Dict[str, float]) -> Dict[str, float]:
        """Gradual correlated drift — moderate difficulty."""
        p       = ATTACK_PARAMS["intermediate"]
        s       = self._state[prn]
        elapsed = time.time() - self._start_time
        iv      = self.intensity

        s["drift"] += p["drift_rate"] * elapsed * iv * 0.1
        f["DO"]    += s["drift"] * 10
        f["TCD"]   += s["drift"] * 5
        f["CN0"]   += s["drift"] * 0.02
        f["PD"]    += s["drift"] * 2000

        noise   = np.random.normal(0, p["correlation_factor"] * iv)
        f["EC"] += noise
        f["LC"] += noise * 0.8
        f["PC"] += noise * 1.2
        return f

    def _sophisticated(self, prn: int, f: Dict[str, float]) -> Dict[str, float]:
        """Smooth sinusoidal multi-feature distortion — hardest to detect."""
        p       = ATTACK_PARAMS["sophisticated"]
        s       = self._state[prn]
        elapsed = time.time() - self._start_time
        iv      = self.intensity

        s["smooth"]  = min(1.0, elapsed / 30.0)
        s["phase"]  += p["smooth_rate"]
        sm, ph       = s["smooth"], s["phase"]

        f["DO"]  += 800   * sm * np.sin(ph)       * iv
        f["TCD"] += 400   * sm * np.sin(ph * 1.3) * iv
        f["CN0"] += 3     * sm * np.sin(ph * 0.7) * iv
        d         = p["multi_feature_distortion"] * sm * iv
        f["EC"]  += d * np.sin(ph * 1.1)
        f["LC"]  += d * np.sin(ph * 0.9)
        f["PC"]  += d * np.sin(ph * 1.2)
        f["PD"]  += 50000 * sm * np.sin(ph * 0.5) * iv

        for k in f:  # tiny realistic noise
            f[k] += np.random.normal(0, max(1.0, abs(f[k]) * 0.0005))
        return f

    # ── Status ─────────────────────────────────────────────────────────────────
    def get_status(self) -> Dict:
        return {
            "active":        self.active,
            "type":          self.attack_type,
            "affected_prns": self.affected_prns,
            "intensity":     self.intensity,
        }
