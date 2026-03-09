"""
ML Model loader and stub
Replace this with actual PyTorch model loading when ready
"""
import numpy as np
from typing import Optional
import os
from config import MODEL_PATH, DETECTION_THRESHOLD


class StubModel:
    """Stub model that simulates ML inference behavior
    
    This will be replaced with actual PyTorch model.
    The interface remains the same: predict(window) -> risk_score
    """
    
    def __init__(self):
        self.threshold = DETECTION_THRESHOLD
    
    def predict(self, window: np.ndarray) -> float:
        """
        Predict risk score from a window of GNSS data
        
        Args:
            window: numpy array of shape (30, 7) containing GNSS features
                    Features: [DO, PD, CN0, TCD, EC, LC, PC]
        
        Returns:
            risk_score: float between 0 and 1
        """
        if window is None or window.shape[0] < 30:
            return 0.0
        
        # Stub logic: detect anomalies based on statistical properties
        # Real model will use trained neural network
        
        # Calculate feature statistics
        means = np.mean(window, axis=0)
        stds = np.std(window, axis=0)
        
        # Calculate changes in recent timesteps
        recent_window = window[-10:]
        earlier_window = window[:10]
        
        recent_means = np.mean(recent_window, axis=0)
        earlier_means = np.mean(earlier_window, axis=0)
        
        # Detect sudden changes (simplified heuristic)
        changes = np.abs(recent_means - earlier_means)
        
        # Normalize by typical variation
        normalized_changes = changes / (stds + 1e-6)
        
        # Features most sensitive to attacks (indices)
        # 0: DO, 2: CN0, 3: TCD, 4-6: correlations
        sensitive_features = [0, 2, 3, 4, 5, 6]
        
        # Calculate risk based on changes in sensitive features
        risk_scores = normalized_changes[sensitive_features]
        
        # Combine risks (weighted average)
        weights = np.array([0.3, 0.25, 0.2, 0.1, 0.1, 0.05])  # DO, CN0, TCD get more weight
        combined_risk = np.sum(risk_scores * weights)
        
        # Add variance-based risk
        variance_risk = np.mean(stds[sensitive_features]) / 10.0
        
        # Total risk score
        total_risk = (combined_risk + variance_risk) / 2.0
        
        # Normalize to [0, 1]
        risk_score = min(1.0, max(0.0, total_risk / 5.0))
        
        # Add small random noise to make it look more realistic
        risk_score += np.random.normal(0, 0.02)
        risk_score = np.clip(risk_score, 0.0, 1.0)
        
        return float(risk_score)


class RealModel:
    """Real PyTorch model (to be implemented when model file is available)"""
    
    def __init__(self, model_path: str):
        """Load trained PyTorch model"""
        # Uncomment when model is ready:
        # import torch
        # self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # self.model = torch.load(model_path, map_location=self.device)
        # self.model.eval()
        pass
    
    def predict(self, window: np.ndarray) -> float:
        """Run inference on model"""
        # Uncomment when model is ready:
        # import torch
        # with torch.no_grad():
        #     x = torch.FloatTensor(window).unsqueeze(0).to(self.device)
        #     output = self.model(x)
        #     risk_score = torch.sigmoid(output).item()
        # return risk_score
        pass


class ModelLoader:
    """Manages model loading and inference"""
    
    def __init__(self):
        self.model: Optional[StubModel] = None
        self.model_type = "stub"
        self.load_model()
    
    def load_model(self):
        """Load model - use real model if available, otherwise use stub"""
        if os.path.exists(MODEL_PATH):
            try:
                # Try to load real model
                self.model = RealModel(MODEL_PATH)
                self.model_type = "real"
                print(f"✓ Loaded real model from {MODEL_PATH}")
            except Exception as e:
                print(f"⚠ Failed to load real model: {e}")
                print("  Using stub model instead")
                self.model = StubModel()
                self.model_type = "stub"
        else:
            print(f"ℹ Model file not found at {MODEL_PATH}")
            print("  Using stub model for demonstration")
            self.model = StubModel()
            self.model_type = "stub"
    
    def predict(self, window: np.ndarray) -> float:
        """Run inference"""
        if self.model is None:
            return 0.0
        return self.model.predict(window)
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None
    
    def get_model_info(self) -> dict:
        """Get information about loaded model"""
        return {
            "loaded": self.is_loaded(),
            "type": self.model_type,
            "path": MODEL_PATH if self.model_type == "real" else "N/A"
        }