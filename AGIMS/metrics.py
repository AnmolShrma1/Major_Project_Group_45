# AGIMS/metrics.py
import torch
import numpy as np

class DetectionMetrics:
    """
    Calculate attack detection metrics for GNSS spoofing system.
    """
    def __init__(self, risk_mode='absolute', attack_threshold=0.2):
        """
        Args:
            risk_mode: 'absolute' or 'delta'
            attack_threshold: Threshold for classifying as attack
                - absolute mode: risk > threshold means attack
                - delta mode: risk_change > threshold means attack starting
        """
        self.risk_mode = risk_mode
        self.attack_threshold = attack_threshold
        self.reset()
    
    def reset(self):
        """Reset all metrics for new epoch"""
        self.detections = []  # (true_label, pred_score, delay)
        self.false_alarms = []
        self.true_positives = []
        self.true_negatives = []
        self.false_positives = []
        self.false_negatives = []
    
    def update(self, predictions, targets, window_indices=None):
        """
        Update metrics with batch predictions.
        
        Args:
            predictions: Model outputs (batch_size, 1)
            targets: Ground truth risk values (batch_size, 1)
            window_indices: Optional window start indices for delay calculation
        """
        predictions = predictions.cpu().numpy().flatten()
        targets = targets.cpu().numpy().flatten()
        
        for i, (pred, target) in enumerate(zip(predictions, targets)):
            if self.risk_mode == 'absolute':
                # In absolute mode, high target = attack present
                is_attack = target > 0.5  # Risk > 0.5 indicates attack
                detected = pred > self.attack_threshold
            else:
                # In delta mode, positive change = attack starting
                is_attack = target > self.attack_threshold
                detected = pred > self.attack_threshold
            
            # Record classification
            if is_attack and detected:
                self.true_positives.append((pred, target))
            elif is_attack and not detected:
                self.false_negatives.append((pred, target))
            elif not is_attack and detected:
                self.false_positives.append((pred, target))
            else:
                self.true_negatives.append((pred, target))
    
    def compute(self):
        """Compute final metrics"""
        tp = len(self.true_positives)
        tn = len(self.true_negatives)
        fp = len(self.false_positives)
        fn = len(self.false_negatives)
        
        total = tp + tn + fp + fn
        
        # Basic classification metrics
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # False alarm rate (on clean windows)
        far = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        # Detection rate
        detection_rate = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'detection_rate': detection_rate,
            'false_alarm_rate': far,
            'true_positives': tp,
            'false_positives': fp,
            'true_negatives': tn,
            'false_negatives': fn
        }
    
    def __str__(self):
        """Pretty print metrics"""
        metrics = self.compute()
        return (
            f"Detection Rate: {metrics['detection_rate']:.2%} | "
            f"False Alarm Rate: {metrics['false_alarm_rate']:.2%} | "
            f"F1: {metrics['f1_score']:.3f} | "
            f"Acc: {metrics['accuracy']:.2%}"
        )


class AttackDelayAnalyzer:
    """
    Analyze detection delay for attacks.
    Tracks how many windows it takes to detect an attack after it starts.
    """
    def __init__(self, window_size=30):
        self.window_size = window_size
        self.attack_starts = []  # (prn_id, start_idx)
        self.detections = []     # (prn_id, detection_idx)
        self.delays = []
    
    def register_attack(self, prn_id, start_idx):
        """Register when an attack started"""
        self.attack_starts.append((prn_id, start_idx))
    
    def register_detection(self, prn_id, detection_idx):
        """Register when attack was detected"""
        self.detections.append((prn_id, detection_idx))
    
    def compute_delays(self):
        """Compute detection delays for all attacks"""
        delays = []
        for prn_id, start_idx in self.attack_starts:
            # Find first detection after attack start
            detections = [d_idx for d_prn, d_idx in self.detections 
                         if d_prn == prn_id and d_idx >= start_idx]
            
            if detections:
                first_detection = min(detections)
                delay = (first_detection - start_idx) * self.window_size  # Convert to samples
                delays.append(delay)
            else:
                delays.append(None)  # Missed attack
        
        self.delays = delays
        
        # Calculate statistics
        detected_delays = [d for d in delays if d is not None]
        
        if detected_delays:
            return {
                'mean_delay': np.mean(detected_delays),
                'median_delay': np.median(detected_delays),
                'min_delay': np.min(detected_delays),
                'max_delay': np.max(detected_delays),
                'std_delay': np.std(detected_delays),
                'detection_rate': len(detected_delays) / len(delays)
            }
        else:
            return {
                'mean_delay': float('inf'),
                'median_delay': float('inf'),
                'min_delay': float('inf'),
                'max_delay': float('inf'),
                'std_delay': 0,
                'detection_rate': 0
            }