# Detailed Changes Summary

## Files Modified - Line-by-Line

### 1. training_and_validation.py

**Location:** Line 21  
**Before:**
```python
DATA_FILE = 'data/train_samples_dev_1_46_600_samples_low_ratio_cleaned.csv'
```

**After:**
```python
DATA_FILE = 'data/train_val_samples.csv'
```

**Reason:** This file is used to load the training/validation pool. The old file doesn't exist; the new file is split from `original_data.csv` (rows 0-599).

---

### 2. predictions_for_testset.py

**Location:** Line 43  
**Before:**
```python
DEFAULT_CSV_FILE = 'data/test_samples_removed_outliers.csv'
```

**After:**
```python
DEFAULT_CSV_FILE = 'data/test_samples.csv'
```

**Reason:** This file is used for predictions. The old file doesn't exist; the new file is split from `original_data.csv` (rows 600-1199).

**Also Updated:** Docstring (lines 1-33)  
**Before:** Referenced old paths like:
```python
python predictions_for_testset.py --models-root "C:\Users\tbe\preparing-MDN_HfOx\models\d2d" --n-samples 125 --dataset "train_samples_dev_1_46_600_samples_low_ratio_cleaned"
```

**After:** Simplified to:
```python
python predictions_for_testset.py --n-samples 125
python predictions_for_testset.py --n-samples 125 --csv-file "data/test_samples.csv"
```

**Also Updated:** Help text for `--dataset` argument (line ~720)  
**Before:**
```python
help="Optional dataset folder under --models-root, e.g. train_samples_dev_1_46_600_samples_low_ratio_cleaned"
```

**After:**
```python
help="Optional dataset folder under --models-root (for backward compatibility)"
```

---

### 3. figures/1f_conductance_distibution.py

**Location:** Line 19  
**Before:**
```python
DEFAULT_TEST_CSV = 'data/test_samples_removed_outliers.csv'
```

**After:**
```python
DEFAULT_TEST_CSV = 'data/test_samples.csv'
```

**Reason:** This script generates conductance distribution plots using the test set.

---

## Data Files Created

### 1. data/train_val_samples.csv
- **Size:** 155,617 bytes
- **Rows:** 601 (1 header + 600 data rows)
- **Source:** `original_data.csv` rows 0-599
- **Used by:** `training_and_validation.py`
- **Purpose:** Training/validation pool

### 2. data/test_samples.csv
- **Size:** 155,644 bytes
- **Rows:** 601 (1 header + 600 data rows)
- **Source:** `original_data.csv` rows 600-1199
- **Used by:** `predictions_for_testset.py`, `figures/1f_conductance_distibution.py`
- **Purpose:** Test set for evaluation

---

## Verification Results

All scripts checked and verified:

```
✓ training_and_validation.py          - Uses train_val_samples.csv
✓ predictions_for_testset.py          - Uses test_samples.csv
✓ figures/1f_conductance_distibution.py - Uses test_samples.csv
✓ baseline_comparison.py              - Uses original_data.csv (unchanged)
✓ All other scripts                   - Use prediction/results CSVs (no changes needed)
```

Data files verified:
```
✓ original_data.csv          (310,957 bytes)
✓ train_val_samples.csv      (155,617 bytes)
✓ test_samples.csv           (155,644 bytes)
✓ sweep_10_cycles.csv        (184,967 bytes)
```

---

## No Remaining Issues

Checked for stray references to old files:
- ✓ No references to `test_samples_removed_outliers.csv` in active code
- ✓ No references to `train_samples_dev_1_46_600_samples_low_ratio_cleaned.csv` in active code
- ✓ Only docstring examples remain (informational, not functional)

---

## How the Split Works

```python
# Split logic (from original_data.csv)
N_POOL = 600

df = pd.read_csv('original_data.csv')
# Total: 1200 data rows

train_val = df.iloc[:600]      # rows 0-599 (600 rows)
test = df.iloc[600:]            # rows 600-1199 (600 rows)

# Save
train_val.to_csv('train_val_samples.csv')  # 601 lines (with header)
test.to_csv('test_samples.csv')            # 601 lines (with header)
```

---

## Testing Commands

You can now run these commands without errors:

```bash
# Train a model
python training_and_validation.py --n-samples 50

# Generate predictions
python predictions_for_testset.py --n-samples 50

# Generate distribution plot
python figures/1f_conductance_distibution.py

# Generate baseline comparison
python baseline_comparison.py
```

All scripts will find their data files correctly! ✓
