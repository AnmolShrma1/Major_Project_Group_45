# AGIMS — Adaptive GNSS Integrity Monitoring System
### Machine Learning Based GPS Spoofing Detection for Mission-Critical IoT Systems

**B.Tech Major Project – Computer Science & Engineering**  
**Jaypee University of Information Technology, Waknaghat**  
**December 2025**

---

# Overview

AGIMS (Adaptive GNSS Integrity Monitoring System) is a machine-learning-driven framework designed to detect **GPS/GNSS spoofing attacks in real-time** for mission-critical IoT environments.

GPS spoofing is a severe cyber-physical threat capable of disrupting **navigation, timing, and control systems** used in military and autonomous infrastructure.  
This project integrates **machine learning, signal analysis, and cybersecurity monitoring** to provide a **lightweight real-time spoofing detection system**.

The system analyzes **GNSS signal parameters** and detects anomalies indicating spoofing or signal manipulation.

---

# Key Features

• Real-time GPS spoofing detection  
• Multi-model machine learning detection pipeline  
• Deep learning (LSTM) based temporal anomaly detection  
• GNSS signal feature analysis (CN₀, Doppler, PRN behaviour)  
• Live spoofing attack simulation dashboard  
• WebSocket-based real-time monitoring interface  
• PRN-wise anomaly tracking  
• Secure logging and signal integrity monitoring  
• Designed for **mission-critical IoT environments**

---

# System Architecture

The system consists of four major components:

GNSS Signal Logs
↓
Feature Extraction & Preprocessing
↓
Machine Learning / Deep Learning Detection
↓
Real-Time Monitoring Dashboard (AGIMS App)


### 1. Data Acquisition

GNSS receiver logs containing satellite signal parameters are collected under different conditions:

• Normal operation  
• Signal interference / jamming  
• SDR-based spoofing attacks  

Supported constellations include:

- GPS
- Galileo
- GLONASS
- BeiDou
- QZSS

---

### 2. Feature Extraction

The system analyzes multiple GNSS signal features:

| Feature | Description |
|------|------|
| PRN | Satellite identifier |
| DO | Doppler offset |
| PD | Pseudorange deviation |
| RX | Receiver timestamp |
| TOW | Time of week |
| CP | Carrier phase |
| PC | Pseudorange correction |
| PIP | Signal integrity parameter |
| TCD | Timing correction difference |
| CN0 | Carrier-to-Noise ratio |

Temporal derivatives are also generated to capture **signal instability patterns**.

---

### 3. Machine Learning Models

Multiple ML models were trained and evaluated for spoofing detection:

| Model | Accuracy | Strength |
|------|------|------|
| **LightGBM** | 97.7% | Fastest inference |
| **XGBoost** | 93.6% | Strong generalization |
| **Random Forest** | 90.5% | Stable baseline |
| **Linear SVC** | 72.2% | Linear benchmark |

---

### 4. Deep Learning Model (AGIMS)

The final detection pipeline uses an **LSTM-based temporal model** which analyzes sequences of GNSS signals.

Advantages:

• Captures temporal signal drift  
• Detects gradual spoofing attacks  
• Handles sequential satellite behavior  
• Suitable for real-time streaming environments

---

# Real-Time Monitoring Application

The project includes a **browser-based monitoring dashboard** built using:

- **FastAPI (Backend)**
- **WebSockets**
- **HTML / CSS / JavaScript**

The dashboard provides:

• Live GNSS signal simulation  
• Real-time spoofing detection alerts  
• Signal integrity visualization  
• Attack severity classification  
• PRN-level monitoring

---

# Repository Structure

```
Major_Project_Group_45
│
├── AGIMS
│   ├── train.py
│   ├── model.py
│   ├── data_pipeline.py
│   ├── metrics.py
│   └── Cleaned_GPS_Spoofing_Dataset.csv
│
├── AGIMS_App
│   ├── backend
│   │   ├── main.py
│   │   ├── inference.py
│   │   ├── attack_simulator.py
│   │   ├── data_simulator.py
│   │   ├── model_loader.py
│   │   ├── websocket_manager.py
│   │   ├── schemas.py
│   │   └── utils.py
│   │
│   └── frontend
│       ├── index.html
│       ├── style.css
│       └── app.js
│
├── Models
│   └── ML training notebooks
│
├── ResearchPapers
│   └── Reference papers
│
└── README.md

```

# Installation

Clone Repository
git clone https://github.com/AnmolShrma1/Major_Project_Group_45.git
cd Major_Project_Group_45

# Install Dependencies

pip install fastapi
pip install uvicorn
pip install pandas
pip install numpy
pip install torch
pip install scikit-learn
pip install websockets


# Training the Detection Model

cd AGIMS
python train.py

This trains the LSTM-based GNSS spoofing detection model.

# Running the Real-Time Monitoring Dashboard

Navigate to the backend folder:

cd AGIMS_App/backend

Run the FastAPI server:

uvicorn main:app --reload

Open the dashboard in your browser:

http://localhost:8000

# Authors

Anmol Sharma
Akanksha Sharma
Rashi Sharma
Simran Suri

Department of Computer Science & Engineering
Jaypee University of Information Technology

# Supervisor

Prof. Dr. Pradeep Kumar Gupta

Keywords
GPS Spoofing • GNSS Security • Machine Learning • LSTM • Cyber-Physical Systems • IoT Security • Satellite Navigation • Signal Integrity Monitoring
