"""
Decision Engine — converts threat assessments into actionable outputs.
"""
from typing import Dict
from config import DECISION_ACTIONS


class DecisionEngine:

    def decide(self, threat: Dict) -> Dict:
        level    = threat["threat_level"]
        lh       = threat["likelihood"]
        impact   = threat["impact_score"]
        decision = self._decision_text(level, lh)
        return {
            "final_decision":     decision,
            "recommended_action": DECISION_ACTIONS[level],
            "alert_flag":         level in ("HIGH", "CRITICAL"),
            "confidence":         round((lh * impact) ** 0.5, 3),
        }

    @staticmethod
    def _decision_text(level: str, lh: float) -> str:
        if level == "LOW":      return "NORMAL – No spoofing detected"
        if level == "MEDIUM":   return f"CAUTION – Anomaly detected (likelihood {lh:.0%})"
        if level == "HIGH":     return f"WARNING – Probable spoofing attack (likelihood {lh:.0%})"
        return f"CRITICAL – Active spoofing confirmed (likelihood {lh:.0%})"
