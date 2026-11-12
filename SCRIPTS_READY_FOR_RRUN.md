# Scripts Ready for --rrun

## ✓ Verification Complete

All scripts have been checked and updated. The data split from the old repository (test vs. train/val files) has been recreated from `original_data.csv` using the same split logic as `baseline_comparison.py`.

## Data Structure

### Files Created:
```
data/
├── original_data.csv          (1200 rows - original full dataset)
├── train_val_samples.csv      (600 rows - rows 0-599, for training/validation)
└── test_samples.csv           (600 rows - rows 600-1199, for testing)
```

### Split Logic:
- **Rows 0-599** → `train_val_samples.csv` (used by `training_and_validation.py`)
- **Rows 600-1199** → `test_samples.csv` (used by `predictions_for_testset.py`)

This matches the `N_POOL = 600` logic in `baseline_comparison.py`.

## Script Updates

### ✓ training_and_validation.py
- **Line 21:** `DATA_FILE = 'data/train_val_samples.csv'`
- **Purpose:** Trains MDN models using the training/validation pool
- **Ready to run:** YES

### ✓ predictions_for_testset.py
- **Line 43:** `DEFAULT_CSV_FILE = 'data/test_samples.csv'`
- **Purpose:** Generates predictions on the test set
- **Ready to run:** YES

### ✓ figures/1f_conductance_distibution.py
- **Line 19:** `DEFAULT_TEST_CSV = 'data/test_samples.csv'`
- **Purpose:** Generates conductance distribution plots
- **Ready to run:** YES

### ✓ baseline_comparison.py
- **Line 33:** `TRAIN_CSV = 'data/original_data.csv'`
- **Note:** Uses full dataset (not split) - no changes needed
- **Ready to run:** YES

### ✓ Other scripts
- `evaluate_predictions_crps.py` - Uses prediction CSVs
- `compute_r_squared.py` - Uses prediction CSVs
- `compute_specific_predictions_new_split.py` - Uses model files
- All figure scripts - Use output CSVs from predictions/results directories

## How to Test

You can now safely press "Run" (or use `--rrun`) on any of these scripts:

```powershell
# Train a single model with 50 samples
python training_and_validation.py --n-samples 50

# Generate predictions on test set
python predictions_for_testset.py --n-samples 50

# Generate conductance distribution plot
python figures/1f_conductance_distibution.py

# Run baseline comparison
python baseline_comparison.py
```

## Training Workflow

### Step 1: Train Models
```powershell
# Train with a single sample size
python training_and_validation.py --n-samples 125

# Or train with all sample sizes (PowerShell)
$sample_sizes = @(8, 12, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 316, 400, 500)
foreach ($n in $sample_sizes) {
    python training_and_validation.py --n-samples $n
}
```

### Step 2: Generate Predictions
```powershell
# Generate predictions with a single sample size
python predictions_for_testset.py --n-samples 125

# Or generate for all sample sizes
foreach ($n in $sample_sizes) {
    python predictions_for_testset.py --n-samples $n
}
```

### Step 3: Evaluate Metrics
```powershell
# Compute CRPS metrics
python evaluate_predictions_crps.py

# Compute R² metrics
python compute_r_squared.py
```

### Step 4: Generate Figures
```powershell
python baseline_comparison.py
python figures/1f_conductance_distibution.py
python figures/visualize_predictions.py
python figures/crps_and_r2_plot.py
```

## Data Split Verification

```
original_data.csv (1200 rows)
        ↓
    Split at row 600
        ↙          ↘
   600 rows      600 rows
       ↓            ↓
train_val_samples.csv (rows 0-599)    test_samples.csv (rows 600-1199)
   │                                      │
   └→ Used by training_and_validation.py  └→ Used by predictions_for_testset.py
       - Training pool                        - Test set evaluation
       - Validation splits (80/20 per model)  - Fixed test samples (600 rows)
```

## Key Differences from Old Repository

**Old setup (with removed_outliers):**
- `train_val_samples_removed_outliers.csv` - Training/validation data
- `test_samples_removed_outliers.csv` - Test data

**New setup (without removed_outliers):**
- `original_data.csv` - Complete raw dataset
- `train_val_samples.csv` - Training/validation split (derived from original)
- `test_samples.csv` - Test split (derived from original)

The split logic remains identical: rows 0-599 for training/validation, rows 600+ for testing.

## Files Modified

1. `training_and_validation.py` - Updated DATA_FILE path
2. `predictions_for_testset.py` - Updated DEFAULT_CSV_FILE path + docstring
3. `figures/1f_conductance_distibution.py` - Updated DEFAULT_TEST_CSV path

## Files Created

1. `data/train_val_samples.csv` - Training/validation split
2. `data/test_samples.csv` - Test set split
3. `split_data.py` - Script used for splitting (kept for reference)
4. `verify_data_setup.py` - Verification script
5. `DATA_UPDATE_REPORT.md` - Detailed update report
6. `SCRIPTS_READY_FOR_RRUN.md` - This file

## ✓ All Checks Passed

- [x] Data files exist and are readable
- [x] Split matches expected rows (600/600)
- [x] All script references updated
- [x] No stray references to removed_outliers files
- [x] Documentation consistent
- [x] Ready to run all scripts with --rrun
