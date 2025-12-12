Machine Learning Techniques for Detecting GPS Spoofing Attacks in Mission-Critical Military IoT Devices
Major Project – B.Tech (CSE)

Department of Computer Science & Engineering
Jaypee University of Information Technology, Waknaghat
December 2025

1. Overview

This repository contains the implementation and analysis of a machine-learning-based framework designed to detect GPS/GNSS spoofing attacks in mission-critical military IoT systems.
The objective is to develop a lightweight, real-time, and high-accuracy detection pipeline that can operate reliably on resource-constrained defense IoT devices.

GPS spoofing is a critical cyber-physical threat capable of disrupting navigation, timing, and mission operations. This project integrates Machine Learning, signal analysis, and cybersecurity to deliver an effective detection system.

2. Key Features

Real-time detection of GPS spoofing attacks

Multi-model ML pipeline (LightGBM, XGBoost, Random Forest, LinearSVC)

Exploratory Data Analysis (EDA) and feature-importance ranking

PRN-level spoofing behavior and anomaly visualization

Real-time alert generation

Secure log processing & pattern analysis

Designed for deployment on military IoT systems

3. System Architecture
3.1 Data Acquisition

GNSS receiver logs collected under normal, jammed, and spoofed conditions

Includes multiple constellations: GPS, Galileo, GLONASS, BeiDou, QZSS

Extracted core GNSS signal features such as CN₀, Doppler, PRN, PD, CP, TCD

3.2 Preprocessing

Cleaning and normalization

Outlier removal

Redundant features removed (EC, LC, PQP)

3.3 Machine Learning Models

LightGBM – highest accuracy and fastest inference

XGBoost – strong generalization

Random Forest – interpretable and stable baseline

Linear SVC – linear benchmark model

3.4 Real-Time Detection Layer

Streams GNSS logs

Performs live inference on each signal batch

Generates spoofing alerts with severity levels

3.5 Cybersecurity Layer

Secure logging

Intrusion monitoring

PRN-wise spoofing analysis

4. Dataset Summary

The dataset used includes GNSS observations captured at Yunnan University with:

Normal operation

Commercial jamming

SDR-based spoofing using HackRF One

Final selected features:
PRN, DO, PD, RX, TOW, CP, PC, PIP, TCD, CN0

5. Model Performance
Model	Accuracy	Key Strengths
LightGBM	97.72%	Fastest & most accurate, ideal for real-time detection
XGBoost	93.64%	Robust with non-linear feature handling
Random Forest	90.57%	Strong baseline, interpretable
Linear SVC	72.23%	Weak for complex/non-linear spoofing patterns
6. Repository Structure
├── data/                    # Raw + processed datasets
├── notebooks/               # EDA, training, evaluation notebooks
├── models/                  # Saved ML models
├── scripts/
│   ├── preprocess.py        # Data cleaning + feature processing
│   ├── train_models.py      # Model training pipeline
│   ├── realtime_detect.py   # Real-time spoofing detection
│   └── log_analyzer.py      # Spoofing log analysis
├── results/                 # Plots and visual outputs
├── README.md
└── requirements.txt

7. Usage Instructions
Step 1 — Install Dependencies
pip install -r requirements.txt

Step 2 — Preprocess Data
python scripts/preprocess.py

Step 3 — Train the Models
python scripts/train_models.py

Step 4 — Run Real-Time Detection
python scripts/realtime_detect.py

Step 5 — Analyze Logs
python scripts/log_analyzer.py

8. Real-Time Alert Example
[SPOOFING ALERT]
Satellite PRN: 2
Severity: HIGH
Timestamp: 2025-11-20 19:32:04

9. Limitations

Dataset is imbalanced (normal >> spoofed)

Some models struggle with unseen PRNs

No physical GNSS receiver testing conducted

Environmental noise & multipath not fully simulated

10. Future Scope

Integration with real GNSS receivers (hardware-in-loop)

Deep learning architectures (CNN, LSTM, Transformers)

Multi-sensor fusion with IMU and map data

Cloud-based GPS threat monitoring platform

Adaptive thresholding for dynamic spoofing environments

11. Authors

Rashi Sharma (221030262)

Anmol Sharma (221030285)

Akanksha Sharma (221031017)

Simran Suri (221030243)

Supervisor:
Prof. Dr. Pradeep Kumar Gupta
