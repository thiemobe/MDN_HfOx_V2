# Publication Plots Generation Report

## Summary
All required plots for the MDN_HfOx_V2 publication have been successfully generated. The repository has been cleaned up and contains only necessary files for publication, with the new split (raw dataset without outlier removal).

## Generated Plots by Category

### Main Results Plots

#### 1. CRPS and R² vs Training Set Size (Baseline Comparison)
**Location**: `figures/Baseline_comparison/`
**Generated Files** (30 total: 15 PNG + 15 SVG):
- K-component comparison plots (9):
  - `crps_vs_n_SET_k_components.png/svg`
  - `crps_vs_n_SET_k_components_inset.png/svg`
  - `crps_vs_n_RESET_k_components.png/svg`
  - `crps_vs_n_RESET_k_components_inset.png/svg`
  - `crps_vs_n_SET_and_RESET_k_components.png/svg`
  - `crps_vs_n_SET_and_RESET_k_components_inset.png/svg`
  - `r2_vs_n_SET_k_components_inset.png/svg`
  - `r2_vs_n_RESET_k_components_inset.png/svg`
  - `r2_vs_n_SET_and_RESET_k_components_inset.png/svg`

- Sigma ablation (QR comparison) plots (6):
  - `crps_vs_n_SET_sigma_ablation_qr_inset.png/svg`
  - `crps_vs_n_RESET_sigma_ablation_qr_inset.png/svg`
  - `crps_vs_n_SET_and_RESET_sigma_ablation_qr_inset.png/svg`
  - `r2_vs_n_SET_sigma_ablation_qr_inset.png/svg`
  - `r2_vs_n_RESET_sigma_ablation_qr_inset.png/svg`
  - `r2_vs_n_SET_and_RESET_sigma_ablation_qr_inset.png/svg`

#### 2. Overall CRPS and R² (New Split)
**Location**: `figures/CRPS_and_R2/`
**Generated Files** (2):
- `crps_and_r2_new_split.png`
- `crps_and_r2_new_split.svg`
**Contains**: Combined CRPS and R² plots for the test set

### Supplementary Material Figures

#### Figure 1: K-Component Comparison
**Location**: `figures/Supplementary_material/Figure_1_K_components_comparison/`
**Files**:
- `crps_vs_n_SET_and_RESET_k_components_inset.png/svg`
- `r2_vs_n_SET_and_RESET_k_components_inset.png/svg`
- `qualitative_SET_sample0242_k_components.png/svg`
- Device 45_40 variant:
  - `device_45_40/crps_vs_n_SET_and_RESET_k_components.png/svg`
  - `device_45_40/r2_vs_n_SET_and_RESET_k_components.png/svg`
  - `device_45_40/qualitative_SET_sample0000_k_components.png/svg`

#### Figure 2: Sigma Ablation Comparison (MDN vs 2 Gaussians Shared Sigma vs QNN)
**Location**: `figures/Supplementary_material/Figure_2_Sigma_ablation_comparison/`
**Files**:
- `crps_vs_n_SET_and_RESET_sigma_ablation_qr_inset.png/svg`
- `r2_vs_n_SET_and_RESET_sigma_ablation_qr_inset.png/svg`
- `qualitative_SET_sample0242_sigma_ablation_shared_only.png/svg`
- Device 45_40 variant:
  - `device_45_40/crps_vs_n_SET_and_RESET_sigma_ablation.png/svg`
  - `device_45_40/r2_vs_n_SET_and_RESET_sigma_ablation.png/svg`
  - `device_45_40/qualitative_SET_sample0000_sigma_ablation.png/svg`

#### Figure 3: Device 45_40 Analysis
**Location**: `figures/Supplementary_material/Figure_3_Device_45_40_analysis/`
**Distribution Plots**:
- `conductance_distribution_train_samples_dev_45_40_1000_samples_low_ratio_vs_original_data.png/svg` ✅ **KEY PLOT**
- Additional variants:
  - `conductance_distribution_dev_45_40_600_samples_low_ratio.png/svg`
  - `conductance_distribution_dev_45_40_1000_samples_low_ratio_train_only.png/svg`

**CRPS and R² for Device 45_40** (4):
- `crps_and_r2_device_45_40/crps_vs_n_SET.png/svg`
- `crps_and_r2_device_45_40/crps_vs_n_RESET.png/svg`
- `crps_and_r2_device_45_40/crps_vs_n_SET_and_RESET.png/svg`
- `crps_and_r2_device_45_40/r2_vs_n_SET_and_RESET.png/svg`

#### Figure 4: Seed Variation Analysis
**Location**: `figures/Supplementary_material/Figure_4_Seed_variation/`
**Files** (4 - as specified by user):
- `seed_variation_mu_sample0001_RESET.png/svg` ✅ **KEY PLOT**
- `seed_variation_p_sample0001_RESET.png/svg` ✅ **KEY PLOT**
- `seed_variation_mu_sample0009_SET.png/svg` ✅ **KEY PLOT**
- `seed_variation_p_sample0009_SET.png/svg` ✅ **KEY PLOT**

Also in direct location:
- `figures/Seed_variation/seed_variation_*.png/svg` (4 files)

### Additional Analysis Plots

#### 3D Validation Example Plots
**Location**: `figures/3d_and_observation_vs_prediction_new_split/`
**Generated Files** (10):
- SVG 3D plots (main results):
  - `validation_examples_3d_set_view1.svg`
  - `validation_examples_3d_set_view2.svg`
  - `validation_examples_3d_reset_view1.svg`
  - `validation_examples_3d_reset_view2.svg`
- PNG example plots:
  - `SET/SET_V0.70_Gbefore9.0.png/svg`
  - `SET/SET_V1.10_Gbefore9.0.png/svg`
  - `SET/SET_V1.30_Gbefore9.0.png/svg`
  - `RESET/RESET_V0.60_Gbefore108.2.png/svg`
  - `RESET/RESET_V1.10_Gbefore108.2.png/svg`
  - `RESET/RESET_V1.40_Gbefore108.2.png/svg`

#### Individual Sample Predictions
**Location**: `figures/Individual_samples_new_split/`
**Generated Files** (8):
- `mdn2_n125_SET_sample0242.png/svg`
- `mdn2_n125_RESET_sample0029.png/svg`
- `mdn2_n125_RESET_sample0048.png/svg`
- `mdn2_n125_RESET_sample0180.png/svg`
- `mdn2_n500_SET_sample0242.png/svg`
- `mdn2_n500_RESET_sample0029.png/svg`
- `mdn2_n500_RESET_sample0048.png/svg`
- `mdn2_n500_RESET_sample0180.png/svg`

#### IV Curves
**Location**: `figures/IV/`
**Files** (2):
- `IV_SET_current.svg`
- `IV_RESET_current.svg`

#### Conductance Distribution
**Location**: `figures/Conductance_distribution/`
**Files** (2):
- `conductance_distribution.png/svg`
- `conductance_distribution_train_samples_dev_45_40_1000_samples_low_ratio_vs_original_data.png/svg` ✅

## Data Files

### Main Dataset
- `data/original_data.csv`: Training and test data (1200 rows)
- Split: Rows 0-599 for training/validation, rows 600-1199 for test set

### Device-Specific Data
- `data/d2d_original_data_1000/train_samples_dev_45_40_1000_samples_low_ratio.csv`: Device 45_40 data (1000 samples)

## Scripts and Infrastructure

### Core Scripts
1. **baseline_comparison.py**
   - Generates k-component and sigma ablation comparison plots
   - Trains baseline models and caches predictions
   - Provides training infrastructure for other scripts

2. **compute_specific_predictions_new_split.py**
   - Retrains mdn2 model for specific n and run
   - Generates validation example predictions for 3D plots
   - Produces: `results/validation_examples_new_split_model_run{run}_{n}samples.csv`

3. **figures/visualize_predictions.py**
   - Generates seed variation plots (mu and p components)
   - Supports ensemble PDF visualization
   - Output: Seed variation plots for specified samples

4. **figures/3d_plot_and_indiv_predictions.py**
   - Creates 3D surface plots of validation examples
   - Requires validation_examples CSV as input
   - Output: 3D SVG plots and individual prediction plots

5. **figures/1f_conductance_distibution.py**
   - Plots and compares conductance distributions
   - Supports device comparison (device 45_40 vs original)
   - Output: Distribution comparison plots

6. **figures/crps_and_r2_plot.py**
   - Generates overall CRPS and R² plots from cached predictions
   - Uses discover_n_values() to find training set sizes
   - Output: Combined CRPS/R² plot

## Verification Status

### ✅ Completed Tasks
- [x] Remove outlier removal approach (raw dataset)
- [x] Update dataset in V2 repository
- [x] Retrain models with new dataset
- [x] Generate updated CRPS and R² plots
- [x] Generate 3D validation example plots
- [x] Generate distribution comparison for device 45_40
- [x] Include seed variation plots (mu and p only)
- [x] Create supplementary material figures
- [x] Clean up repository (remove unnecessary files)
- [x] Integrate training functions into baseline_comparison.py
- [x] Test all scripts for functionality
- [x] Generate all plots in PNG and SVG formats
- [x] Add device data for device 45_40

### ✅ Generated Plot Summary
- **Total PNG plots**: 63
- **Total SVG plots**: 69
- **Total plots**: 132 (counting both formats)
- **Baseline comparison plots**: 30 (k-components + sigma ablation)
- **Supplementary material figures**: 27 plots + SVGs
- **Device analysis plots**: 8 (device 45_40)
- **Seed variation plots**: 4 (mu_1, mu_2, p_1, p_2)
- **3D validation plots**: 4 main views + individual examples
- **Overall metrics plots**: 2 (CRPS and R²)

## Quality Checks

✅ All plots generated successfully
✅ Both PNG and SVG formats available
✅ Seed variation plots show only mu and p (no coefficient of variation)
✅ Device 45_40 specific plots included
✅ 3D validation example plots generated (view1 and view2)
✅ All scripts execute without errors
✅ Model retraining validated against cached predictions
✅ Data consistency verified

## Next Steps

1. Review supplementary material figures for publication quality
2. Verify plot legends and labels are publication-ready
3. Confirm device 45_40 analysis is complete and included
4. Update manuscript references to figure numbers
5. Prepare README for publication
6. Archive old scripts/files not needed for publication

## Notes

- All scripts use Python 3.14.3 from `.venv`
- New split: 600 train/val rows (rows 0-599), 600 test rows (rows 600-1199)
- No outlier removal (raw dataset as per V2 specification)
- Cached predictions automatically discovered and used where applicable
- All plots use consistent styling (Times New Roman font, publication-ready colors)
