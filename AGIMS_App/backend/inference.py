"""
Inference engine - runs ML model on sliding windows
"""
import numpy as np
from typing import Dict, Optional
from model_loader import ModelLoader
from utils import SlidingWindowBuffer
from config import WINDOW_SIZE, DETECTION_THRESHOLD


class InferenceEngine:
    """Manages model inference on streaming data"""
    
    def __init__(self):
        self.model_loader = ModelLoader()
        self.window_buffer = SlidingWindowBuffer(WINDOW_SIZE)
        self.latest_predictions: Dict[int, float] = {}
        self.detection_counts: Dict[int, int] = {}
    
    def process_datapoint(self, prn: int, features: Dict[str, float]) -> Optional[float]:
        """
        Process a new datapoint and run inference if window is ready
        
        Args:
            prn: PRN identifier
            features: Dictionary of GNSS features
        
        Returns:
            risk_score if inference ran, None otherwise
        """
        # Add to sliding window
        self.window_buffer.add_point(prn, features)
        
        # Check if we have enough data
        if not self.window_buffer.is_ready(prn):
            return None
        
        # Get window and run inference
        window = self.window_buffer.get_window(prn)
        risk_score = self.model_loader.predict(window)
        
        # Store latest prediction
        self.latest_predictions[prn] = risk_score
        
        # Track detections
        if risk_score >= DETECTION_THRESHOLD:
            self.detection_counts[prn] = self.detection_counts.get(prn, 0) + 1
        
        return risk_score
    
    def get_latest_prediction(self, prn: int) -> float:
        """Get the most recent prediction for a PRN"""
        return self.latest_predictions.get(prn, 0.0)
    
    def is_attack_detected(self, risk_score: float) -> bool:
        """Determine if risk score indicates an attack"""
        return risk_score >= DETECTION_THRESHOLD
    
    def get_detection_stats(self) -> Dict:
        """Get detection statistics"""
        return {
            "total_detections": sum(self.detection_counts.values()),
            "detections_per_prn": self.detection_counts.copy(),
            "prns_monitored": list(self.latest_predictions.keys())
        }
    
    def reset(self):
        """Reset inference engine state"""
        self.window_buffer.clear()
        self.latest_predictions.clear()
        self.detection_counts.clear()
    
    def get_model_info(self) -> dict:
        """Get model information"""
        return self.model_loader.get_model_info()