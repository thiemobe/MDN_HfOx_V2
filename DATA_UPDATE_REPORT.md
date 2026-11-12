# Data File Update Report

## Summary
All scripts have been checked and updated to work with the new data structure. The repository now uses:
- **Training/Validation data**: `data/train_val_samples.csv` (600 samples)
- **Test data**: `data/test_samples.csv` (600 samples)

These files are split from `original_data.csv` using the same split logic as `baseline_comparison.py` (N_POOL = 600).

## Data Split Details
- **original_data.csv**: 1200 data rows + 1 header row
- **train_val_samples.csv**: rows 0-599 (601 lines including header)
- **test_samples.csv**: rows 600-1199 (601 lines including header)

## Updated Files

### Core Training/Prediction Scripts
✅ **training_and_validation.py**
- Line 21: `DATA_FILE = 'data/train_val_samples.csv'`
- Used for: Training models, validating with cross-validation splits
- Status: Ready to run

✅ **predictions_for_testset.py**
- Line 43: `DEFAULT_CSV_FILE = 'data/test_samples.csv'`
- Used for: Generating predictions on test set
- Status: Ready to run

✅ **baseline_comparison.py**
- Line 33: `TRAIN_CSV = 'data/original_data.csv'` (unchanged - uses full dataset for baseline)
- Note: This script uses the full original_data.csv for baseline training/testing
- Status: No changes needed - works with existing data

### Figure Generation Scripts
✅ **figures/1f_conductance_distibution.py**
- Line 19: `DEFAULT_TEST_CSV = 'data/test_samples.csv'`
- Status: Ready to run

✅ **figures/3d_plot_and_indiv_predictions.py**
- Uses validation examples from `results/` directory
- Status: No changes needed

✅ **figures/visualize_predictions.py**
- Uses prediction CSVs from `predictions/` directory
- Status: No changes needed

✅ **figures/crps_and_r2_plot.py**
- Uses CRPS and R² results from `results/` directories
- Status: No changes needed

### Analysis Scripts
✅ **evaluate_predictions_crps.py**
- Uses prediction CSVs from `predictions/` directory
- Status: No changes needed

✅ **compute_r_squared.py**
- Uses prediction CSVs from `predictions/` directory
- Status: No changes needed

✅ **compute_specific_predictions_new_split.py**
- Uses model predictions
- Status: No changes needed

## How to Run

### Step 1: Train MDN Models
```powershell
# Train models with different sample sizes
$sample_sizes = @(8, 12, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 316, 400, 500)
foreach ($n in $sample_sizes) {
    python training_and_validation.py --n-samples $n
}
```

### Step 2: Generate Predictions on Test Set
```powershell
# Generate predictions for all sample sizes
$sample_sizes = @(8, 12, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 316, 400, 500)
foreach ($n in $sample_sizes) {
    python predictions_for_testset.py --n-samples $n
}
```

### Step 3: Evaluate Predictions
```powershell
# Compute CRPS metrics
python evaluate_predictions_crps.py

# Compute R² metrics
python compute_r_squared.py
```

### Step 4: Generate Figures
```powershell
# Generate baseline comparison plots
python baseline_comparison.py

# Generate conductance distribution plots
python figures/1f_conductance_distibution.py

# Generate visualization plots
python figures/visualize_predictions.py
```

## Data Flow Diagram

```
original_data.csv (1200 rows)
    │
    ├─→ Split at row 600 ─────────────────────────┐
    │                                              │
    ├─→ train_val_samples.csv (rows 0-599)      ├─→ test_samples.csv (rows 600-1199)
    │   (used by training_and_validation.py)       (used by predictions_for_testset.py)
    │   - Train N samples from this pool           - Test set for evaluation
    │   - Validation split 80/20 per model         - 600 test samples
    │
    └─→ Also available: sweep_10_cycles.csv
        (cycle-by-cycle data for detailed analysis)
```

## Files Created
- `data/train_val_samples.csv` - Training/validation pool (600 samples)
- `data/test_samples.csv` - Test set (600 samples)
- `split_data.py` - Script used to create the split (for reference)

## Verification Checklist
- [x] All data files exist and are accessible
- [x] File splits match the N_POOL = 600 logic from baseline_comparison.py
- [x] All hardcoded data file paths updated
- [x] Documentation strings updated
- [x] No references to removed outlier files remain
- [x] All scripts ready to run with --rrun

## Notes
- The training/validation split within the train_val_samples.csv is handled dynamically by training_and_validation.py
- Each model trains on N samples, with additional N*VAL_RATIO samples for validation
- The test set is fixed and not split - all models evaluate against the same 600 test samples
