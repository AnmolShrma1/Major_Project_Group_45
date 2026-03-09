"""
GNSS spoofing attack simulator
Injects various types of attacks into the data stream
"""
import numpy as np
import time
from typing import Dict, List, Optional
from config import ATTACK_PARAMS


class AttackSimulator:
    """Simulates various GPS spoofing attack patterns"""
    
    def __init__(self):
        self.active = False
        self.attack_type = "none"
        self.affected_prns: List[int] = []
        self.intensity = 1.0
        self.attack_start_time = 0
        self.attack_state: Dict[int, Dict] = {}
    
    def start_attack(self, attack_type: str, prns: Optional[List[int]] = None, intensity: float = 1.0):
        """Start a spoofing attack"""
        self.active = True
        self.attack_type = attack_type
        self.affected_prns = prns if prns else []
        self.intensity = intensity
        self.attack_start_time = time.time()
        
        # Initialize attack state for each affected PRN
        for prn in self.affected_prns:
            self.attack_state[prn] = {
                "phase": 0,
                "accumulated_drift": 0,
                "smooth_factor": 0
            }
    
    def stop_attack(self):
        """Stop the current attack"""
        self.active = False
        self.attack_type = "none"
        self.affected_prns = []
        self.attack_state.clear()
    
    def apply_attack(self, prn: int, features: Dict[str, float]) -> Dict[str, float]:
        """Apply attack modifications to features if PRN is affected"""
        if not self.active or prn not in self.affected_prns:
            return features
        
        if self.attack_type == "simplistic":
            return self._apply_simplistic_attack(prn, features)
        elif self.attack_type == "intermediate":
            return self._apply_intermediate_attack(prn, features)
        elif self.attack_type == "sophisticated":
            return self._apply_sophisticated_attack(prn, features)
        
        return features
    
    def _apply_simplistic_attack(self, prn: int, features: Dict[str, float]) -> Dict[str, float]:
        """Simplistic attack: Sudden large jumps in key features"""
        params = ATTACK_PARAMS["simplistic"]
        
        # Sudden CN0 spike
        features["CN0"] += params["CN0_spike"] * self.intensity
        
        # Large Doppler jump
        features["DO"] += params["DO_jump"] * self.intensity * np.random.choice([-1, 1])
        
        # TCD jump
        features["TCD"] += params["TCD_jump"] * self.intensity * np.random.choice([-1, 1])
        
        # Add noise to correlations
        features["EC"] += np.random.normal(0, 0.3 * self.intensity)
        features["LC"] += np.random.normal(0, 0.3 * self.intensity)
        features["PC"] += np.random.normal(0, 0.2 * self.intensity)
        
        return features
    
    def _apply_intermediate_attack(self, prn: int, features: Dict[str, float]) -> Dict[str, float]:
        """Intermediate attack: Gradual drift with correlated anomalies"""
        params = ATTACK_PARAMS["intermediate"]
        state = self.attack_state[prn]
        
        # Calculate time since attack started
        elapsed = time.time() - self.attack_start_time
        
        # Gradual drift
        drift_amount = params["drift_rate"] * elapsed * self.intensity
        state["accumulated_drift"] += drift_amount * 0.1
        
        # Apply correlated drifts
        features["DO"] += state["accumulated_drift"] * 100
        features["TCD"] += state["accumulated_drift"] * 0.5
        features["CN0"] += state["accumulated_drift"] * 0.2
        
        # Small correlated anomalies
        correlation_noise = np.random.normal(0, params["correlation_factor"] * self.intensity)
        features["EC"] += correlation_noise
        features["LC"] += correlation_noise * 0.8
        features["PC"] += correlation_noise * 1.2
        
        # Pseudorange derivative anomaly
        features["PD"] += drift_amount * 50
        
        return features
    
    def _apply_sophisticated_attack(self, prn: int, features: Dict[str, float]) -> Dict[str, float]:
        """Sophisticated attack: Smooth, multi-feature, harder to detect"""
        params = ATTACK_PARAMS["sophisticated"]
        state = self.attack_state[prn]
        
        # Calculate smooth progression
        elapsed = time.time() - self.attack_start_time
        state["smooth_factor"] = min(1.0, elapsed / 30.0)  # Ramp up over 30 seconds
        state["phase"] += params["smooth_rate"]
        
        smooth = state["smooth_factor"]
        phase = state["phase"]
        
        # Smooth sinusoidal distortions
        do_distortion = 300 * smooth * np.sin(phase) * self.intensity
        tcd_distortion = 2 * smooth * np.sin(phase * 1.3) * self.intensity
        cn0_distortion = 3 * smooth * np.sin(phase * 0.7) * self.intensity
        
        features["DO"] += do_distortion
        features["TCD"] += tcd_distortion
        features["CN0"] += cn0_distortion
        
        # Multi-feature coordinated distortion
        distortion_factor = params["multi_feature_distortion"] * smooth * self.intensity
        
        features["EC"] += distortion_factor * np.sin(phase * 1.1)
        features["LC"] += distortion_factor * np.sin(phase * 0.9)
        features["PC"] += distortion_factor * np.sin(phase * 1.2)
        features["PD"] += 200 * smooth * np.sin(phase * 0.5) * self.intensity
        
        # Add very small noise to make it look natural
        for key in features:
            features[key] += np.random.normal(0, 0.1 * smooth)
        
        return features
    
    def get_status(self) -> Dict:
        """Get current attack status"""
        return {
            "active": self.active,
            "type": self.attack_type,
            "affected_prns": self.affected_prns,
            "intensity": self.intensity
        }