"""
Live GNSS data simulator
Generates realistic satellite signal data streams
"""
import numpy as np
import time
from typing import Dict
from config import FEATURE_RANGES, PRN_IDS


class GNSSDataSimulator:
    """Simulates realistic GNSS signal data for multiple PRNs"""
    
    def __init__(self):
        self.start_time = time.time()
        self.base_values: Dict[int, Dict[str, float]] = {}
        self.drift_states: Dict[int, Dict[str, float]] = {}
        self._initialize_prns()
    
    def _initialize_prns(self):
        """Initialize base values and drift states for each PRN"""
        for prn in PRN_IDS:
            self.base_values[prn] = {
                "DO": np.random.uniform(*FEATURE_RANGES["DO"]),
                "PD": np.random.uniform(*FEATURE_RANGES["PD"]),
                "CN0": np.random.uniform(*FEATURE_RANGES["CN0"]),
                "TCD": np.random.uniform(*FEATURE_RANGES["TCD"]),
                "EC": np.random.uniform(*FEATURE_RANGES["EC"]),
                "LC": np.random.uniform(*FEATURE_RANGES["LC"]),
                "PC": np.random.uniform(*FEATURE_RANGES["PC"]),
            }
            
            # Drift states for smooth temporal variation
            self.drift_states[prn] = {
                "DO_drift": np.random.uniform(-50, 50),
                "CN0_drift": np.random.uniform(-0.5, 0.5),
                "TCD_drift": np.random.uniform(-0.2, 0.2),
            }
    
    def generate_sample(self, prn: int) -> Dict[str, float]:
        """Generate a single data sample for a PRN with realistic variation"""
        if prn not in self.base_values:
            raise ValueError(f"PRN {prn} not initialized")
        
        base = self.base_values[prn]
        drift = self.drift_states[prn]
        
        # Add smooth temporal variation
        t = time.time() - self.start_time
        
        # Doppler with drift and sinusoidal variation
        DO = base["DO"] + drift["DO_drift"] + 100 * np.sin(0.1 * t) + np.random.normal(0, 50)
        
        # Pseudorange derivative with small variation
        PD = base["PD"] + 50 * np.sin(0.05 * t) + np.random.normal(0, 100)
        
        # CN0 with drift and noise
        CN0 = base["CN0"] + drift["CN0_drift"] + np.random.normal(0, 1.5)
        CN0 = np.clip(CN0, FEATURE_RANGES["CN0"][0], FEATURE_RANGES["CN0"][1])
        
        # TCD with drift
        TCD = base["TCD"] + drift["TCD_drift"] + np.random.normal(0, 0.5)
        
        # Correlation values with small variations
        EC = base["EC"] + np.random.normal(0, 0.05)
        LC = base["LC"] + np.random.normal(0, 0.05)
        PC = base["PC"] + np.random.normal(0, 0.03)
        
        # Update drift states slowly
        drift["DO_drift"] += np.random.normal(0, 2)
        drift["DO_drift"] = np.clip(drift["DO_drift"], -100, 100)
        
        drift["CN0_drift"] += np.random.normal(0, 0.1)
        drift["CN0_drift"] = np.clip(drift["CN0_drift"], -2, 2)
        
        drift["TCD_drift"] += np.random.normal(0, 0.05)
        drift["TCD_drift"] = np.clip(drift["TCD_drift"], -1, 1)
        
        return {
            "DO": float(DO),
            "PD": float(PD),
            "CN0": float(CN0),
            "TCD": float(TCD),
            "EC": float(EC),
            "LC": float(LC),
            "PC": float(PC),
        }
    
    def get_timestamp(self) -> float:
        """Get current simulation timestamp"""
        return time.time() - self.start_time
    
    def reset(self):
        """Reset the simulator"""
        self.start_time = time.time()
        self._initialize_prns()