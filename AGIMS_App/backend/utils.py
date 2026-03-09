"""
Utility functions for AGIMS application
"""
import numpy as np
from typing import List, Dict
from collections import deque


class SlidingWindowBuffer:
    """Maintains a sliding window of data points for each PRN"""
    
    def __init__(self, window_size: int):
        self.window_size = window_size
        self.buffers: Dict[int, deque] = {}
    
    def add_point(self, prn: int, features: Dict[str, float]):
        """Add a data point to the buffer for a specific PRN"""
        if prn not in self.buffers:
            self.buffers[prn] = deque(maxlen=self.window_size)
        
        # Convert features dict to array
        feature_array = [
            features['DO'],
            features['PD'],
            features['CN0'],
            features['TCD'],
            features['EC'],
            features['LC'],
            features['PC']
        ]
        self.buffers[prn].append(feature_array)
    
    def get_window(self, prn: int) -> np.ndarray:
        """Get the current window for a PRN as numpy array"""
        if prn not in self.buffers or len(self.buffers[prn]) < self.window_size:
            return None
        
        return np.array(list(self.buffers[prn]))
    
    def is_ready(self, prn: int) -> bool:
        """Check if window is full for a PRN"""
        return prn in self.buffers and len(self.buffers[prn]) == self.window_size
    
    def clear(self):
        """Clear all buffers"""
        self.buffers.clear()


def normalize_features(features: Dict[str, float]) -> Dict[str, float]:
    """Normalize features (placeholder - implement based on training data stats)"""
    # In production, use actual mean/std from training data
    # For now, return as-is since model is a stub
    return features


def calculate_trend(values: List[float], window: int = 5) -> float:
    """Calculate trend direction from recent values"""
    if len(values) < window:
        return 0.0
    
    recent = values[-window:]
    x = np.arange(len(recent))
    y = np.array(recent)
    
    # Simple linear regression
    slope = np.polyfit(x, y, 1)[0]
    return float(slope)