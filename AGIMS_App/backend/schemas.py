"""
AGIMS — Pydantic schemas for all API requests, responses, and WebSocket messages.
"""
from pydantic import BaseModel
from typing import Dict, List, Optional
from enum import Enum


class AttackType(str, Enum):
    NONE          = "none"
    SIMPLISTIC    = "simplistic"
    INTERMEDIATE  = "intermediate"
    SOPHISTICATED = "sophisticated"


class ThreatAssessment(BaseModel):
    threat_level: str
    likelihood:   float
    impact_score: float
    mitre_tactic: str


class DecisionOutput(BaseModel):
    final_decision:     str
    recommended_action: str
    alert_flag:         bool
    confidence:         float


class LiveDataMessage(BaseModel):
    prn:             int
    timestamp:       float
    risk_score:      float
    attack_detected: bool
    raw_features:    Dict[str, float]
    current_attack:  str
    data_source:     str
    threat:          ThreatAssessment
    decision:        DecisionOutput


class AttackStartRequest(BaseModel):
    attack_type: AttackType
    prns:        Optional[List[int]] = None
    intensity:   Optional[float]     = 1.0


class StatusResponse(BaseModel):
    simulation_running: bool
    attack_active:      bool
    attack_type:        Optional[str]
    affected_prns:      List[int]
    model_loaded:       bool
    model_type:         str
    data_source:        str
    prn_ids:            List[int]


class StartRequest(BaseModel):
    demo_mode: Optional[bool] = False
