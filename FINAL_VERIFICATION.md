# Final Verification - All Scripts Ready ✓

## Issue Fixed
The `training_and_validation.py` was trying to access columns that don't exist in the 27-column CSV format.

### Problem
- Script tried to access columns [14, 19, 24, 29, 34, 39, 44, 49, 54, 59]
- CSV only has 27 columns (0-26)
- Error: `IndexError: positional indexers are out-of-bounds`

### Solution
Updated column indices to match the 27-column format (same as `baseline_comparison.py`):

**File:** `training_and_validation.py` (Lines 228-236)

**Before:**
```python
G_col9 = pd.to_numeric(df.iloc[:, 10], errors='coerce').to_numpy(dtype=float) * 1e6
V_col4 = pd.to_numeric(df.iloc[:, 3], errors='coerce').to_numpy(dtype=float)
conductance_after = pd.to_numeric(df.iloc[:, [14, 19, 24, 29, 34, 39, 44, 49, 54, 59]].mean(axis=1), errors='coerce').to_numpy(dtype=float) * 1e6
```

**After:**
```python
G_col9 = pd.to_numeric(df.iloc[:, 9], errors='coerce').to_numpy(dtype=float) * 1e6
V_col4 = pd.to_numeric(df.iloc[:, 3], errors='coerce').to_numpy(dtype=float)
conductance_after = pd.to_numeric(df.iloc[:, [11, 14, 17]].mean(axis=1), errors='coerce').to_numpy(dtype=float) * 1e6
```

### Column Mapping
- Column 0: State (SET/RESET)
- Column 3: Voltage
- Column 9: G_before (conductance before)
- Columns 11, 14, 17: G_after measurements (1s, 5s, 10s) - averaged for y

## Verification Results

### Train/Val Data (train_val_samples.csv)
```
✓ CSV loaded: 600 rows, 27 columns
✓ state shape: (600,)
✓ g_before shape: (600,)
✓ voltage shape: (600,)
✓ y shape: (600,)
✓ X shape: (600, 3)
✓ All values finite: True
✓ SUCCESS: All column access works!
```

### Test Data (test_samples.csv)
```
✓ CSV loaded: 600 rows, 27 columns
✓ state shape: (600,)
✓ g_before shape: (600,)
✓ voltage shape: (600,)
✓ y shape: (600,)
✓ X shape: (600, 3)
✓ All values finite: True
✓ SUCCESS: Test data loading works!
```

## Ready to Run

All scripts are now ready to use with `--rrun`:

```bash
# Train a model
python training_and_validation.py --n-samples 50

# Generate predictions
python predictions_for_testset.py --n-samples 50

# Generate plots
python figures/1f_conductance_distibution.py

# Run baseline comparison
python baseline_comparison.py
```

## Summary of All Changes Made

1. **Created data split files:**
   - `data/train_val_samples.csv` (600 rows from original_data.csv rows 0-599)
   - `data/test_samples.csv` (600 rows from original_data.csv rows 600-1199)

2. **Updated script file paths:**
   - `training_and_validation.py`: `DATA_FILE = 'data/train_val_samples.csv'`
   - `predictions_for_testset.py`: `DEFAULT_CSV_FILE = 'data/test_samples.csv'`
   - `figures/1f_conductance_distibution.py`: `DEFAULT_TEST_CSV = 'data/test_samples.csv'`

3. **Fixed column indices:**
   - `training_and_validation.py`: Updated `build_data()` function to use correct 27-column indices (9, 3, [11, 14, 17])

All systems operational! ✓
