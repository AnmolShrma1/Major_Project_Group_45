"""
Pydantic schemas for API requests and responses
"""
from pydantic import BaseModel
from typing import Dict, List, Optional
from enum import Enum


class AttackType(str, Enum):
    NONE = "none"
    SIMPLISTIC = "simplistic"
    INTERMEDIATE = "intermediate"
    SOPHISTICATED = "sophisticated"


class GNSSFeatures(BaseModel):
    DO: float
    PD: float
    CN0: float
    TCD: float
    EC: float
    LC: float
    PC: float


class DataPoint(BaseModel):
    prn: int
    timestamp: float
    features: GNSSFeatures


class LiveDataMessage(BaseModel):
    prn: int
    timestamp: float
    risk_score: float
    attack_detected: bool
    raw_features: Dict[str, float]
    current_attack: str


class AttackStartRequest(BaseModel):
    attack_type: AttackType
    prns: Optional[List[int]] = None  # If None, apply to all PRNs
    intensity: Optional[float] = 1.0  # Multiplier for attack strength


class StatusResponse(BaseModel):
    simulation_running: bool
    attack_active: bool
    attack_type: Optional[str]
    affected_prns: List[int]
    model_loaded: bool


class StartRequest(BaseModel):
    demo_mode: Optional[bool] = False