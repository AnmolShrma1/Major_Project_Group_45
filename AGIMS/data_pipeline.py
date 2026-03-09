# AGIMS/data_pipeline.py
import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler
from torch.utils.data import Dataset

WINDOW = 30 #Because spoofing attacks evolve over time, not in one instant

RAW_FEATURES = ["DO","PD","RX","TOW","CP","EC","LC","PC","PIP","PQP","TCD","CN0"]
DELTA_FEATURES = ["dDO","dPD","dCN0","dTCD","dEC","dLC","dPC"] 
#dDO = DO(t) - DO(t-1), Spoofing causes abrupt signal changes model learns to detect signal jumps

RISK_MAP = {0:0.1, 1:0.4, 2:0.7, 3:0.9}
#Instead of predicting class labels, the model predicts risk score

class GNSSDataset(Dataset):
    def __init__(self, csv_path, scaler=None, random_seed=42, attack_prob=0.3, 
                 risk_mode='absolute', train_prns=None):
        """
        Args:
            csv_path: Path to CSV file
            scaler: Pre-fitted StandardScaler. If None AND train_prns provided, 
                    fits only on train_prns. If both None, fits on all data.
            random_seed: Seed for reproducible attack injection
            attack_prob: Probability of attacking each stream
            risk_mode: 'absolute' (predict final risk) or 'delta' (predict risk change)
            train_prns: List of PRN indices to use for fitting scaler (prevents leakage)
        """
        np.random.seed(random_seed) #Ensures that random attacks injected during training are reproducible
        
        df = pd.read_csv(csv_path)
        df = df.sort_values(["PRN","TOW","RX"]).reset_index(drop=True)
        #Because we want signals ordered like:
        #PRN1: t1, t2, t3, ...
        #PRN2: t1, t2, t3, ...

        df["risk"] = df["Output"].map(RISK_MAP) # map class labels to risk scores (0.1, 0.4, 0.7, 0.9) for regression target

        # Calculate delta features BEFORE attack injection
        for col in ["DO","PD","CN0","TCD","EC","LC","PC"]:
            df[f"d{col}"] = df.groupby("PRN")[col].diff().fillna(0) #Signals are grouped by satellite,Calculates difference between consecutive rows, First row has no previous value

        self.features = RAW_FEATURES + DELTA_FEATURES
        self.risk_mode = risk_mode

        # Create streams first (before scaling)
        self.streams = [] #Each PRN becomes one stream
        
        for stream_idx, (prn, g) in enumerate(df.groupby("PRN")): #Each satellite signal becomes one independent sequence
            g = g.reset_index(drop=True)

            # Inject attacks with proper bounds checking
            if len(g) >= 50 and np.random.rand() < attack_prob:
                start = np.random.randint(0, len(g) - 50) #Randomly chooses attack start position
                self.inject_simplistic_attack(g, start, 40) #Creates a synthetic spoofing attack lasting 40 timesteps

            if len(g) > WINDOW: #Only streams longer than 30 samples are used
                self.streams.append(g)

        # Handle scaler - FIT ONLY ON TRAINING PRNS
        if scaler is None:
            if train_prns is not None:
                # Fit scaler ONLY on training PRNs (no data leakage!)
                train_data = []
                for idx in train_prns:
                    if idx < len(self.streams):
                        # Convert to numpy array to avoid sklearn warning
                        train_data.append(self.streams[idx][self.features].values)
                
                if train_data:
                    train_array = np.vstack(train_data)
                    self.scaler = StandardScaler()
                    self.scaler.fit(train_array)
                else:
                    raise ValueError("No training data found for scaler fitting")
            else:
                # Fallback: fit on all data (has leakage, but for quick testing)
                all_data = np.vstack([s[self.features].values for s in self.streams])
                self.scaler = StandardScaler()
                self.scaler.fit(all_data)
                print("⚠️  WARNING: Scaler fitted on ALL data (including validation). "
                      "This causes data leakage!")
        else:
            self.scaler = scaler

        # Now scale all streams - use .values to avoid sklearn warning
        for s in self.streams:
            s[self.features] = self.scaler.transform(s[self.features].values)

    def __len__(self):
        return sum(len(s) - WINDOW for s in self.streams)

    def __getitem__(self, idx):
        for s in self.streams:
            if idx < len(s) - WINDOW:
                window = s.loc[idx:idx+WINDOW-1, self.features].values
                
                if self.risk_mode == 'delta':
                    # Predict change in risk over the window
                    risk = s.loc[idx+WINDOW-1, "risk"] - s.loc[idx, "risk"]
                    # Clip to reasonable range for training stability
                    risk = np.clip(risk, -1, 1)
                else:
                    # Predict average risk over the window
                    risk = s.loc[idx:idx+WINDOW-1, "risk"].mean()
                
                return (torch.tensor(window, dtype=torch.float32), 
                        torch.tensor([risk], dtype=torch.float32))
            idx -= len(s) - WINDOW
        raise IndexError(f"Index {idx} out of bounds")
    
    def inject_simplistic_attack(self, df, start, length):
        """Inject attack and update risk accordingly"""
        end = min(start + length, len(df))
        actual_length = end - start
        ramp = np.linspace(0, 1, actual_length)
        
        # Modify features MORE AGGRESSIVELY for better detection
        df.loc[start:end-1, "CN0"] += 10 * ramp  # Increased from 3
        df.loc[start:end-1, "TCD"] += 2 * ramp   # Increased from 0.5
        
        # Also modify other features to make attacks more distinct
        df.loc[start:end-1, "DO"] += 5 * ramp
        df.loc[start:end-1, "PD"] += 3 * ramp
        
        # Update risk MORE AGGRESSIVELY
        df.loc[start:end-1, "risk"] = np.clip(
            df.loc[start:end-1, "risk"] + 0.6 * ramp,  # Increased from 0.3
            0, 1
        )
        
        # Recalculate delta features for affected columns
        for col in ["CN0", "TCD", "DO", "PD"]:
            if start > 0:
                df.loc[start, f"d{col}"] = df.loc[start, col] - df.loc[start-1, col]
            for i in range(start+1, end):
                df.loc[i, f"d{col}"] = df.loc[i, col] - df.loc[i-1, col]