import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ===============================
# CONFIGURATION
# ===============================
DATA_FILE = "GPS_Data_Simplified_2D_Feature_Map.xlsx"

# ===============================
# LOAD DATA
# ===============================
df = pd.read_excel(DATA_FILE)
df = df.rename(columns={"Output": "label"})

total_signals = len(df)
spoofed_df = df[df["label"] > 0]
spoof_count = len(spoofed_df)

# ===============================
# 1️⃣ LIKELIHOOD CALCULATION
# ===============================
likelihood = spoof_count / total_signals if total_signals > 0 else 0

# ===============================
# 2️⃣ IMPACT CALCULATION
# (How many unique satellites targeted)
# ===============================
unique_prns_targeted = spoofed_df["PRN"].nunique()
total_unique_prns = df["PRN"].nunique()

impact = unique_prns_targeted / total_unique_prns if total_unique_prns > 0 else 0

# ===============================
# 3️⃣ EXPLOITABILITY
# (Signal irregularity measure)
# ===============================
snr_std = df["SNR"].std() if "SNR" in df.columns else 0
doppler_std = df["Doppler"].std() if "Doppler" in df.columns else 0

exploitability = (snr_std + doppler_std) / 100
exploitability = min(exploitability, 1)

# ===============================
# 4️⃣ ASSET CRITICALITY
# (Satellite exposure factor)
# ===============================
criticality = unique_prns_targeted / total_unique_prns if total_unique_prns > 0 else 0

# ===============================
# 5️⃣ ATTACK SURFACE SCORE
# (Overall system vulnerability indicator)
# ===============================
signal_variability = df[["SNR", "Doppler"]].std().mean() if all(col in df.columns for col in ["SNR", "Doppler"]) else 0
attack_surface = min(signal_variability / 50, 1)

# ===============================
# 6️⃣ ENHANCED RISK MODEL
# Risk = L × I × E × C
# ===============================
risk_score = likelihood * impact * exploitability * criticality

# ===============================
# 7️⃣ RISK LEVEL CLASSIFICATION
# ===============================
if risk_score > 0.6:
    risk_level = "CRITICAL"
elif risk_score > 0.4:
    risk_level = "HIGH"
elif risk_score > 0.2:
    risk_level = "MEDIUM"
else:
    risk_level = "LOW"

# ===============================
# 8️⃣ THREAT CLASSIFICATION
# ===============================
def classify_threat(likelihood, impact):
    if likelihood > 0.5 and impact > 0.5:
        return "Coordinated Multi-Satellite Spoofing"
    elif likelihood > 0.3:
        return "Localized Signal Injection"
    elif impact > 0.4:
        return "High-Impact Targeted Spoofing"
    else:
        return "Low-Level Spoofing Attempt"

threat_type = classify_threat(likelihood, impact)

# ===============================
# 9️⃣ CONFIDENCE SCORE
# ===============================
confidence_score = min((likelihood + exploitability) / 2, 1)

# ===============================
# 🔟 PRINT PROFESSIONAL REPORT
# ===============================
print("\n🛰️  GNSS THREAT MODELING & RISK INTELLIGENCE REPORT")
print("======================================================")
print(f"Total Signals Analyzed        : {total_signals}")
print(f"Spoofed Signals Detected      : {spoof_count}")
print("------------------------------------------------------")
print(f"Likelihood Score              : {round(likelihood,3)}")
print(f"Impact Score                  : {round(impact,3)}")
print(f"Exploitability Score          : {round(exploitability,3)}")
print(f"Asset Criticality Score       : {round(criticality,3)}")
print(f"Attack Surface Score          : {round(attack_surface,3)}")
print("------------------------------------------------------")
print(f"Overall Risk Score            : {round(risk_score,3)}")
print(f"Threat Classification         : {threat_type}")
print(f"Threat Level                  : {risk_level}")
print(f"Confidence Score              : {round(confidence_score,3)}")
print("======================================================\n")

# ===============================
# 1️⃣1️⃣ VISUALIZATION (Single Plot)
# ===============================
plt.figure()
plt.bar(
    ["Likelihood", "Impact", "Exploitability", "Criticality", "Risk Score"],
    [likelihood, impact, exploitability, criticality, risk_score]
)
plt.ylim(0, 1)
plt.title("GNSS Threat Modeling Metrics")
plt.xlabel("Threat Modeling Factors")
plt.ylabel("Normalized Score (0-1)")
plt.show()
