# AGIMS/train.py
import torch
import numpy as np
from torch.utils.data import DataLoader, Subset
import warnings

from data_pipeline import GNSSDataset, WINDOW
from model import IntegrityLSTM
from metrics import DetectionMetrics

# Suppress sklearn warnings
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

def get_stream_indices(dataset, prn_ids):
    """Get all sample indices belonging to specified PRN streams"""
    idxs = []
    offset = 0
    for i, s in enumerate(dataset.streams):
        n = len(s) - WINDOW
        if i in prn_ids:
            idxs.extend(range(offset, offset + n))
        offset += n
    return idxs

def evaluate_with_metrics(model, dataloader, criterion, device, risk_mode, attack_threshold=0.15):
    """
    Evaluate model with both loss and detection metrics.
    
    Returns:
        avg_loss: Average loss over dataset
        metrics: DetectionMetrics object with computed metrics
    """
    model.eval()
    total_loss = 0
    num_batches = 0
    
    # Initialize metrics tracker
    metrics = DetectionMetrics(risk_mode=risk_mode, attack_threshold=attack_threshold)
    
    with torch.no_grad():
        for X, y in dataloader:
            X, y = X.to(device, non_blocking=True), y.to(device, non_blocking=True)
            
            pred = model(X)
            loss = criterion(pred, y)
            
            total_loss += loss.item()
            num_batches += 1
            
            # Update detection metrics
            metrics.update(pred, y)
    
    avg_loss = total_loss / num_batches if num_batches > 0 else 0
    
    return avg_loss, metrics

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    csv_path = r"D:\Major Project\AGIMS\Cleaned_GPS_Spoofing_Dataset.csv"
    
    # Configuration - LOWERED THRESHOLD for better detection
    RISK_MODE = 'delta'  # 'absolute' or 'delta'
    ATTACK_THRESHOLD = 0.15  # Lowered from 0.2 for more sensitive detection
    
    print(f"Configuration: risk_mode={RISK_MODE}, threshold={ATTACK_THRESHOLD}")
    
    # ===================================================================
    # STEP 1: Load data WITHOUT scaling to determine train/val split
    # ===================================================================
    print("\nLoading dataset to determine PRN splits...")
    temp_dataset = GNSSDataset(csv_path, random_seed=42, attack_prob=0.3)
    
    # Split by PRN streams (ensures no data leakage between train/val)
    prn_indices = np.arange(len(temp_dataset.streams))
    np.random.seed(42)
    np.random.shuffle(prn_indices)

    split_idx = int(0.8 * len(prn_indices))
    train_prns = prn_indices[:split_idx]
    val_prns = prn_indices[split_idx:]
    
    print(f"Total PRN streams: {len(temp_dataset.streams)}")
    print(f"Train PRNs: {len(train_prns)}, Val PRNs: {len(val_prns)}")
    
    # ===================================================================
    # STEP 2: Create dataset with scaler fitted ONLY on training PRNs
    # ===================================================================
    print("\n✅ Fitting scaler on TRAINING data only (no leakage)...")
    dataset = GNSSDataset(
        csv_path, 
        random_seed=42, 
        attack_prob=0.3,
        risk_mode=RISK_MODE,
        train_prns=train_prns
    )
    
    print(f"Total samples: {len(dataset)}")
    
    # ===================================================================
    # STEP 3: Create train/val subsets
    # ===================================================================
    train_idx = get_stream_indices(dataset, train_prns)
    val_idx = get_stream_indices(dataset, val_prns)

    print(f"Train samples: {len(train_idx)}, Val samples: {len(val_idx)}")

    train_set = Subset(dataset, train_idx)
    val_set = Subset(dataset, val_idx)

    # Create dataloaders
    train_loader = DataLoader(
        train_set, 
        batch_size=64, 
        shuffle=True, 
        num_workers=4, 
        pin_memory=True
    )
    val_loader = DataLoader(
        val_set, 
        batch_size=64, 
        num_workers=4, 
        pin_memory=True
    )

    # ===================================================================
    # STEP 4: Initialize model with correct output mode
    # ===================================================================
    model = IntegrityLSTM(
        input_size=19, 
        output_mode=RISK_MODE
    ).to(device)
    
    # Choose loss function based on mode
    if RISK_MODE == 'delta':
        criterion = torch.nn.MSELoss()
        print("Using MSE loss (delta mode)")
    else:
        criterion = torch.nn.HuberLoss()
        print("Using Huber loss (absolute mode)")
    
    # Use lower learning rate for better convergence
    optimizer = torch.optim.Adam(model.parameters(), lr=5e-4)
    
    print(f"\nStarting training...")
    print("=" * 80)

    best_val_loss = float('inf')
    best_f1 = 0
    
    for epoch in range(15):  # Increased epochs
        # ===============================================================
        # Training phase
        # ===============================================================
        model.train()
        train_loss = 0
        num_batches = 0
        
        for i, (X, y) in enumerate(train_loader):
            X, y = X.to(device, non_blocking=True), y.to(device, non_blocking=True)

            if epoch == 0 and i == 0:
                print(f"Batch shape: {X.shape}, Device: {X.device}")
                print(f"Target range: [{y.min().item():.3f}, {y.max().item():.3f}]")

            pred = model(X)
            loss = criterion(pred, y)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            num_batches += 1
        
        train_loss /= num_batches
        
        # ===============================================================
        # Validation phase with metrics
        # ===============================================================
        val_loss, val_metrics = evaluate_with_metrics(
            model, val_loader, criterion, device, RISK_MODE, ATTACK_THRESHOLD
        )
        
        metrics_dict = val_metrics.compute()
        
        # Print epoch summary
        print(f"\nEpoch {epoch+1:2d}/{15}")
        print(f"  Loss      | Train: {train_loss:.4f} | Val: {val_loss:.4f}")
        print(f"  Detection | Rate: {metrics_dict['detection_rate']:.2%} | "
              f"False Alarms: {metrics_dict['false_alarm_rate']:.2%}")
        print(f"  Quality   | Precision: {metrics_dict['precision']:.3f} | "
              f"Recall: {metrics_dict['recall']:.3f} | F1: {metrics_dict['f1_score']:.3f}")
        print(f"  Confusion | TP: {metrics_dict['true_positives']}, "
              f"FP: {metrics_dict['false_positives']}, "
              f"TN: {metrics_dict['true_negatives']}, "
              f"FN: {metrics_dict['false_negatives']}")
        
        # Save best model based on F1 score
        if metrics_dict['f1_score'] > best_f1:
            best_f1 = metrics_dict['f1_score']
            best_val_loss = val_loss
            
            # Save only model weights and necessary info (no sklearn objects)
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'train_loss': train_loss,
                'val_loss': val_loss,
                'metrics': metrics_dict,
                'scaler_mean': dataset.scaler.mean_.tolist(),  # Save as list
                'scaler_scale': dataset.scaler.scale_.tolist(),  # Save as list
                'risk_mode': dataset.risk_mode,
                'attack_threshold': ATTACK_THRESHOLD,
                'features': dataset.features
            }, 'best_model.pth')
            print(f"  → ⭐ New best model saved! (F1: {best_f1:.3f})")

    print("\n" + "=" * 80)
    print(f"Training complete!")
    print(f"Best F1 Score: {best_f1:.3f}")
    print(f"Best Val Loss: {best_val_loss:.4f}")
    
    # ===================================================================
    # Final evaluation on validation set
    # ===================================================================
    print("\n" + "=" * 80)
    print("FINAL VALIDATION METRICS:")
    print("=" * 80)
    
    # Load best model - FIX: use weights_only=True
    checkpoint = torch.load('best_model.pth', weights_only=True)
    model.load_state_dict(checkpoint['model_state_dict'])
    
    _, final_metrics = evaluate_with_metrics(
        model, val_loader, criterion, device, RISK_MODE, ATTACK_THRESHOLD
    )
    
    final_dict = final_metrics.compute()
    
    print(f"Detection Rate:     {final_dict['detection_rate']:.2%}")
    print(f"False Alarm Rate:   {final_dict['false_alarm_rate']:.2%}")
    print(f"Precision:          {final_dict['precision']:.3f}")
    print(f"Recall:             {final_dict['recall']:.3f}")
    print(f"F1 Score:           {final_dict['f1_score']:.3f}")
    print(f"Accuracy:           {final_dict['accuracy']:.2%}")
    print("\nInterpretation:")
    print(f"  - Catches {final_dict['detection_rate']:.0%} of attacks")
    print(f"  - Raises false alarms on {final_dict['false_alarm_rate']:.0%} of clean signals")
    
    if final_dict['f1_score'] > 0.7:
        print(f"  - ✅ Good overall performance (F1 > 0.7)")
    elif final_dict['f1_score'] > 0.5:
        print(f"  - ⚠️  Moderate performance (F1 > 0.5)")
    else:
        print(f"  - ❌ Needs improvement (F1 < 0.5)")


if __name__ == "__main__":
    main()