"""
AGIMS — Global Configuration
All paths, constants, and tunable parameters live here.
"""
import os

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH   = os.path.join(BASE_DIR, "model", "best_model.pth")
DATASET_PATH = os.path.join(BASE_DIR, "data", "Cleaned_GPS_Spoofing_Dataset.csv")

# ── PRN IDs (all 18 real PRNs present in the dataset) ─────────────────────────
PRN_IDS  = [2, 3, 4, 6, 7, 8, 9, 11, 12, 16, 17, 19, 20, 25, 26, 27, 30, 31]
NUM_PRNS = len(PRN_IDS)

# ── Simulation timing ──────────────────────────────────────────────────────────
SIMULATION_INTERVAL = 0.3    # seconds between full PRN sweep
WINDOW_SIZE         = 30     # sliding-window length for inference
UPDATE_RATE         = 300    # ms (informational — used by frontend)

# ── Real GNSS reader (serial / mock-API) ───────────────────────────────────────
GNSS_SERIAL_PORT = "COM3"                    # Windows; Linux → "/dev/ttyUSB0"
GNSS_BAUD_RATE   = 9600
GNSS_TIMEOUT     = 2                         # seconds before fallback
GNSS_MOCK_API    = "http://localhost:9000/gnss"

# ── Feature value ranges (calibrated to Cleaned_GPS_Spoofing_Dataset.csv) ─────
FEATURE_RANGES = {
    "DO":  (-700,    3500),
    "PD":  (-500000, 1000000),
    "CN0": (41,      51),
    "TCD": (-800,    3500),
    "EC":  (37000,   226000),
    "LC":  (40000,   224000),
    "PC":  (45000,   237000),
}

# ── Attack injection parameters (scaled to real data magnitudes) ───────────────
ATTACK_PARAMS = {
    "simplistic": {
        "CN0_spike": 5,
        "DO_jump":   1000,
        "TCD_jump":  500,
    },
    "intermediate": {
        "drift_rate":        0.5,
        "correlation_factor": 5000,
    },
    "sophisticated": {
        "smooth_rate":            0.1,
        "multi_feature_distortion": 3000,
    },
}

# ── Detection ──────────────────────────────────────────────────────────────────
DETECTION_THRESHOLD = 0.5

# ── Threat levels (risk_score ranges) ─────────────────────────────────────────
THREAT_LEVELS = {
    "LOW":      (0.0,  0.3),
    "MEDIUM":   (0.3,  0.5),
    "HIGH":     (0.5,  0.75),
    "CRITICAL": (0.75, 1.01),
}

# ── Decision engine actions ────────────────────────────────────────────────────
DECISION_ACTIONS = {
    "LOW":      "Continue monitoring. No immediate action required.",
    "MEDIUM":   "Increase sampling rate and flag for review.",
    "HIGH":     "Activate secondary navigation source. Alert operator.",
    "CRITICAL": "Engage fallback positioning. Isolate affected PRNs. Immediate alert.",
}
