# Script Verification Summary

All scripts required for the publication have been tested and verified to work correctly with the new split (raw dataset without outlier removal).

## Verified Scripts

### 1. baseline_comparison.py
**Status**: ✅ WORKING
**Description**: Generates k-component comparison and sigma ablation plots for supplementary material
**Generated Files**:
- `figures/Baseline_comparison/crps_vs_n_*_k_components*.png/svg` (9 plots)
- `figures/Baseline_comparison/crps_vs_n_*_sigma_ablation_qr_inset.png/svg` (6 plots)
**Key Functions Added**:
- `discover_n_values()`: Discovers training set sizes from cached predictions
- `cache_path(kind, n)`: Returns path to cached predictions
- Training functions: `build_model()`, `make_loss_fn()`, `train_network()`
- Metric functions: `crps_mixture()`, `per_sample_crps()`, `per_sample_mean()`, `r_squared()`
**Usage**:
```bash
python baseline_comparison.py
```

### 2. compute_specific_predictions_new_split.py
**Status**: ✅ WORKING
**Description**: Retrains the mdn2 model and generates validation example predictions
**Generated Files**:
- `results/validation_examples_new_split_model_run{run}_{n}samples.csv`
**Key Features**:
- Retrains mdn2 with specific n and run parameters
- Validates that retrained model matches cached predictions
- Outputs mixture parameters (pi, mu, sigma) for validation examples
**Usage**:
```bash
python compute_specific_predictions_new_split.py --n 500 --run 1
```

### 3. figures/visualize_predictions.py
**Status**: ✅ WORKING
**Description**: Visualizes seed variation plots and other prediction comparisons
**Generated Files**:
- `figures/Seed_variation/seed_variation_mu_sample{idx:04d}_{STATE}.png/svg`
- `figures/Seed_variation/seed_variation_p_sample{idx:04d}_{STATE}.png/svg`
**Usage Examples**:
```bash
# Seed variation plots for SET sample 9
python figures/visualize_predictions.py --seed-variation --state set --sample-idx 9

# Seed variation plots for RESET sample 1
python figures/visualize_predictions.py --seed-variation --state reset --sample-idx 1
```

### 4. figures/3d_plot_and_indiv_predictions.py
**Status**: ✅ WORKING
**Description**: Creates 3D surface plots of validation examples
**Generated Files**:
- `figures/3d_and_observation_vs_prediction_new_split/validation_examples_3d_{state}_view{1,2}.svg`
**Usage**:
```bash
python figures/3d_plot_and_indiv_predictions.py --validation-examples --validation-csv results/validation_examples_new_split_model_run1_500samples.csv
```

### 5. figures/1f_conductance_distibution.py
**Status**: ✅ WORKING
**Description**: Plots conductance distributions for device comparison
**Generated Files**:
- `figures/Conductance_distribution/conductance_distribution_{device}_vs_{reference}.png/svg`
**Usage**:
```bash
python figures/1f_conductance_distibution.py --compare-train-csvs "data/d2d_original_data_1000/train_samples_dev_45_40_1000_samples_low_ratio.csv" "data/original_data.csv"
```

### 6. figures/crps_and_r2_plot.py
**Status**: ✅ WORKING
**Description**: Plots CRPS and R² metrics for test set
**Generated Files**:
- `figures/CRPS_and_R2/crps_and_r2_new_split.png/svg`
**Key Features**:
- Uses cached baseline_comparison predictions
- Computes CRPS and R² for all training set sizes
- Generates square layout plots
**Usage**:
```bash
python figures/crps_and_r2_plot.py
```

## Data Files

### Device Data Added
- `data/d2d_original_data_1000/train_samples_dev_45_40_1000_samples_low_ratio.csv`
  - Device 45_40 data (1000 samples, low ratio)
  - Used for device-specific distribution and metric plots

## Key Infrastructure

### baseline_comparison.py Module Functions

All scripts that need training infrastructure import from `baseline_comparison.py`. Key exported functions:

**Data Loading**:
- `load_test_data()`: Load test set (rows 600+)
- `load_training_arrays(n_total)`: Load first n_total training rows
- `parse_original_rows(df)`: Parse CSV into X, y arrays

**Model Training**:
- `build_model(kind)`: Create model architecture
- `make_loss_fn(kind)`: Create loss function
- `train_network(net, loss_fn, X_tr, y_tr, X_val, y_val, shuffle_seed)`: Training loop
- `fit_and_predict(kind, n, run_idx, test_X, test_masks, return_model)`: Full training pipeline

**Metrics**:
- `crps_mixture(y, pi, mu, sigma)`: Closed-form CRPS for Gaussian mixtures
- `per_sample_crps(kind, n, state, y_true)`: Per-sample CRPS from cached predictions
- `per_sample_mean(kind, n, state)`: Predicted means from cached predictions
- `r_squared(y_true, y_pred)`: R² metric

**Caching**:
- `cache_path(kind, n)`: Path to cached predictions
- `discover_n_values()`: Find all training set sizes in cache

### Configuration Constants

- `TRAIN_CSV`: Path to training data
- `N_POOL`: Number of rows in train/validation pool (600)
- `CACHE_DIR`: Directory with cached baseline model predictions
- `PARAMS`: Training hyperparameters (learning rate, batch size, etc.)
- `STATES`: Tuple of states ('set', 'reset')
- `N_RUNS`: Number of training runs per model/n combination (5)
- `VAL_RATIO`: Validation split ratio (0.2)
- `WEIGHT_INIT_SEED`: Random seed for weight initialization (42)

## Testing Checklist

- [x] baseline_comparison.py generates all k_component and sigma_ablation plots
- [x] compute_specific_predictions_new_split.py trains models and generates validation examples
- [x] visualize_predictions.py creates seed variation plots for specified samples
- [x] 3d_plot_and_indiv_predictions.py creates 3D validation example plots
- [x] 1f_conductance_distibution.py compares device and original distributions
- [x] crps_and_r2_plot.py generates metric plots from cached predictions
- [x] All plots generated in both PNG and SVG formats
- [x] Device data (45_40) available and working
- [x] All training functions integrated into baseline_comparison.py
- [x] No outlier removal (raw dataset as per V2 requirements)

## Notes

- All scripts run with the `.venv` virtual environment at `.\.venv\Scripts\python.exe`
- Python version: 3.14.3
- The baseline_comparison.py file was renamed from baseline_comparison_cleaned.py to maintain compatibility with imports
- All cached predictions are pre-computed and stored in `results/baseline_comparison/cache/`
- SVG plots are automatically generated alongside PNG files

## Next Steps for Publication

1. Verify all generated plots are in the correct format (PNG + SVG)
2. Check that seed_variation plots show only upper half (mu and p, without coefficient of variation details)
3. Ensure device-specific plots are included for device 45_40
4. Verify supplementary material figures contain all required plots
5. Update README if necessary to reflect new split and structure
