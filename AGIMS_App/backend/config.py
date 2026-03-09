"""
Global configuration for AGIMS application
"""

# Simulation settings
SIMULATION_INTERVAL = 0.3  # seconds between data points
WINDOW_SIZE = 30  # timesteps for ML model input
NUM_PRNS = 8  # number of satellite PRNs to simulate
UPDATE_RATE = 300  # milliseconds for WebSocket updates

# PRN IDs
PRN_IDS = list(range(1, NUM_PRNS + 1))

# Feature ranges for realistic GNSS data generation
FEATURE_RANGES = {
    "DO": (-2000, 2000),  # Doppler
    "PD": (20000, 25000),  # Pseudorange derivative
    "CN0": (35, 50),  # Carrier-to-noise ratio
    "TCD": (-10, 10),  # Time carrier deviation
    "EC": (0.5, 1.5),  # Early correlation
    "LC": (0.5, 1.5),  # Late correlation
    "PC": (0.8, 1.5),  # Prompt correlation
}

# Attack parameters
ATTACK_PARAMS = {
    "simplistic": {
        "CN0_spike": 15,
        "DO_jump": 1500,
        "TCD_jump": 8
    },
    "intermediate": {
        "drift_rate": 0.5,
        "correlation_factor": 0.3
    },
    "sophisticated": {
        "smooth_rate": 0.1,
        "multi_feature_distortion": 0.2
    }
}

# Model settings
MODEL_PATH = "model/best_model.pth"
DETECTION_THRESHOLD = 0.5  # Risk score threshold for attack detection