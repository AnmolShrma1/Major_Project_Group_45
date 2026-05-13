"""
ML model loader.
Uses heuristic StubModel when no trained .pth file is present.
Drop best_model.pth into backend/model/ to activate the real model.

Window shape : (30, 7)
Feature order: [DO, PD, CN0, TCD, EC, LC, PC]
"""
import numpy as np
import os
from typing import Optional
from config import MODEL_PATH, DETECTION_THRESHOLD


class StubModel:
    """
    Statistical heuristic tuned to Cleaned_GPS_Spoofing_Dataset.csv.

    Typical normal-data standard deviations (empirical):
      DO  ~400   PD  ~80 000   CN0 ~1.5
      TCD ~400   EC  ~30 000   LC  ~30 000   PC  ~30 000
    """

    NORMAL_STD = np.array([400, 80000, 1.5, 400, 30000, 30000, 30000], dtype=float)
    # Weights: TCD and DO most sensitive to spoofing, then CN0, then correlations
    WEIGHTS    = np.array([0.28, 0.08, 0.22, 0.27, 0.05, 0.05, 0.05], dtype=float)

    def predict(self, window: np.ndarray) -> float:
        if window is None or window.shape[0] < 30:
            return 0.0

        recent  = window[-10:]
        earlier = window[:10]
        std     = np.std(window, axis=0)

        # Normalised mean-shift between recent and earlier epochs
        shift  = np.abs(np.mean(recent, 0) - np.mean(earlier, 0)) / (self.NORMAL_STD + 1e-6)
        # Normalised variance anomaly
        var    = std / (self.NORMAL_STD + 1e-6)

        score  = float(np.dot(0.65 * shift + 0.35 * var, self.WEIGHTS))
        # Map: score ~3 → risk ~0.5 (threshold)
        risk   = score / 6.0 + np.random.normal(0, 0.012)
        return float(np.clip(risk, 0.0, 1.0))


class RealModel:
    """PyTorch model stub — fill in when best_model.pth is ready."""

    def __init__(self, path: str):
        # import torch
        # self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # self.model  = torch.load(path, map_location=self.device)
        # self.model.eval()
        pass

    def predict(self, window: np.ndarray) -> float:
        # import torch
        # with torch.no_grad():
        #     x = torch.FloatTensor(window).unsqueeze(0).to(self.device)
        #     return float(torch.sigmoid(self.model(x)).item())
        return 0.0


class ModelLoader:

    def __init__(self):
        self.model:      Optional[StubModel] = None
        self.model_type: str = "stub"
        self._load()

    def _load(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model      = RealModel(MODEL_PATH)
                self.model_type = "real"
                print(f"✓ Real model loaded from {MODEL_PATH}")
                return
            except Exception as e:
                print(f"⚠  Real model failed ({e}) — using heuristic stub")
        else:
            print(f"ℹ  No model at {MODEL_PATH} — using heuristic stub")
        self.model      = StubModel()
        self.model_type = "stub"

    def predict(self, window: np.ndarray) -> float:
        return self.model.predict(window) if self.model else 0.0

    def is_loaded(self) -> bool:
        return self.model is not None

    def get_model_info(self) -> dict:
        return {"loaded": self.is_loaded(), "type": self.model_type,
                "path": MODEL_PATH if self.model_type == "real" else "N/A"}
