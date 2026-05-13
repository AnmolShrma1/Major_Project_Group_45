"""
Threat Modeling Layer.
Maps risk_score → threat level, likelihood, impact, MITRE ATT&CK tactic.
"""
from typing import Dict
from config import THREAT_LEVELS

_MITRE = {
    "LOW":      "T0856 – Spoof Reporting Message (monitoring phase)",
    "MEDIUM":   "T0856 – Spoof Reporting Message (active probing)",
    "HIGH":     "T0860 – Wireless Compromise (signal injection detected)",
    "CRITICAL": "T0860 + T0881 – Service Stop (navigation integrity lost)",
}
_SEVERITY = {"LOW": 0.2, "MEDIUM": 0.45, "HIGH": 0.75, "CRITICAL": 1.0}


class ThreatModel:

    def assess(self, risk_score: float, attack_detected: bool) -> Dict:
        level      = self._level(risk_score)
        likelihood = self._likelihood(risk_score, attack_detected)
        impact     = round(min(1.0, _SEVERITY[level] * (0.5 + likelihood * 0.5)), 3)
        return {
            "threat_level": level,
            "likelihood":   round(likelihood, 3),
            "impact_score": impact,
            "mitre_tactic": _MITRE[level],
        }

    @staticmethod
    def _level(score: float) -> str:
        for lvl, (lo, hi) in THREAT_LEVELS.items():
            if lo <= score < hi:
                return lvl
        return "CRITICAL"

    @staticmethod
    def _likelihood(score: float, detected: bool) -> float:
        return float(min(1.0, score * 1.3 if detected else score))
