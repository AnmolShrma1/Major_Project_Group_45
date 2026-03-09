# AGIMS/model.py
import torch
import torch.nn as nn

class IntegrityLSTM(nn.Module):
    def __init__(self, input_size=19, hidden=64, layers=2, output_mode='absolute'):
        """
        Args:
            input_size: Number of input features
            hidden: Hidden layer size
            layers: Number of LSTM layers
            output_mode: 'absolute' (sigmoid, [0,1]) or 'delta' (no activation, [-1,1])
        """
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden, layers, batch_first=True)
        self.fc = nn.Linear(hidden, 1)
        self.output_mode = output_mode
        
        # Only use sigmoid for absolute risk prediction
        if output_mode == 'absolute':
            self.act = nn.Sigmoid()
        else:
            self.act = None  # No activation for delta mode

    def forward(self, x):
        # x shape: (batch, sequence_length, input_size)
        out, _ = self.lstm(x)
        # Take only the last timestep output
        out = out[:, -1, :]  # shape: (batch, hidden)
        out = self.fc(out)   # shape: (batch, 1)
        
        if self.act is not None:
            out = self.act(out)  # Apply sigmoid only in absolute mode
        
        return out  # [0,1] for absolute, unbounded for delta