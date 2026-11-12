# Conductance Distribution Script - Cleaned & Ready

## Summary
The `figures/1f_conductance_distibution.py` has been completely cleaned up and simplified. All legacy code removed. Two simple modes:

## Mode 1: Plot Single Dataset (Default)

Plot the conductance distribution of `original_data.csv`:

```bash
python figures/1f_conductance_distibution.py
```

**Output:**
- `figures/Conductance_distribution/conductance_distribution_original_data.png`
- `figures/Conductance_distribution/conductance_distribution_original_data.svg`

## Mode 2: Compare Two Datasets

Compare two CSV files side-by-side:

```bash
python figures/1f_conductance_distibution.py --compare-train-csvs "data/d2d_original_data_1000/train_samples_dev_45_40_1000_samples_low_ratio.csv" "data/original_data.csv"
```

**Output:**
- Comparison plot with both distributions overlaid
- PNG and SVG formats

## Command-Line Arguments

### Default Mode
```
--data-csv CSV_PATH           CSV file to plot (default: data/original_data.csv)
--output-dir OUTPUT_DIR       Output directory (default: figures/Conductance_distribution)
--bins N                      Number of histogram bins (default: 50)
```

### Comparison Mode
```
--compare-train-csvs CSV1 CSV2   Two CSV files to compare
--output-dir OUTPUT_DIR          Output directory (default: figures/Conductance_distribution)
--bins N                         Number of histogram bins (default: 50)
```

## What Was Changed

### Removed
- All complex train/test comparison logic
- Multiple file handling and directory scanning
- Legacy configuration and unused functions
- Confusing command-line options

### Kept
- Simple, clear histogram plotting
- PNG and SVG output
- Conductance extraction from column 9
- Comparison functionality

### New Features
- Default mode: just run without arguments
- Clear documentation in docstring
- Descriptive output messages
- Automatic outlier exclusion for better visualization

## Examples

### Plot default dataset
```bash
python figures/1f_conductance_distibution.py
```

### Plot custom dataset
```bash
python figures/1f_conductance_distibution.py --data-csv "data/train_val_samples.csv"
```

### Compare two datasets
```bash
python figures/1f_conductance_distibution.py --compare-train-csvs "data/d2d_original_data_1000/train_samples_dev_45_40_1000_samples_low_ratio.csv" "data/original_data.csv"
```

### Custom bins
```bash
python figures/1f_conductance_distibution.py --bins 100
```

## Ready to Use ✓

The script now:
- ✓ Works immediately when you press "Run" 
- ✓ Has clean, understandable code
- ✓ Supports both single and comparison plots
- ✓ Provides clear console output
- ✓ Generates publication-quality plots
