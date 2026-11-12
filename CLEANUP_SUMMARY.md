# Baseline Comparison Script Cleanup

## Summary
Cleaned up the large `baseline_comparison.py` script (869 lines) into a focused `baseline_comparison_cleaned.py` script (322 lines) that generates only the k_component and sigma_ablation comparison plots needed for the supplementary material.

## Reduction
- **Original file size**: 869 lines
- **Cleaned file size**: 322 lines
- **Reduction**: 62.9% smaller

## What Was Kept
### K-Component Analysis (K=1..5)
- Heteroscedastic Gaussian (hetero, K=1)
- MDN with 2 components (mdn2, K=2)
- MDN with 3 components (mdn3, K=3)
- MDN with 4 components (mdn4, K=4)
- MDN with 5 components (mdn5, K=5)

### Sigma Ablation Study
- MDN with learned σ(x) (mdn2)
- Single Gaussian with constant σ (const)
- 2-component mixture with shared constant σ (mixshared)
- 2-component mixture with per-component constant σ (mixconst)

### Plots Generated (54 files total)
- **CRPS plots** (Continuous Ranked Probability Score)
  - Main plots for SET, RESET, SET_and_RESET
  - Inset plots (zoomed to 100-500 training samples)
  - All with error bands showing std dev across 5 runs

- **R² plots** (Coefficient of Determination)
  - Inset plots for SET, RESET, SET_and_RESET
  - All with error bands

- **Output formats**: Both PNG (100 dpi) and SVG for publication

## What Was Removed
- Training loop and weight optimization
- Capacity control model (hetero_deep)
- Quantile regression predictions loading
- Paired CRPS difference computation
- Qualitative prediction plots
- Predictive interval tables
- Sigma variation plots
- Verify protocol functionality
- Argument parsing for device CSVs and model subsets

## Key Functions Kept
1. **Data Loading**
   - `parse_original_rows()`: Parse raw CSV data
   - `load_test_data()`: Load test set (rows 600+)
   - `cache_path()`: Get cached prediction file paths

2. **Metrics**
   - `crps_mixture()`: Compute CRPS for Gaussian mixtures
   - `crps_quantiles()`: CRPS for quantile regression
   - `per_sample_crps()`: Load and compute CRPS per sample
   - `per_sample_mean()`: Compute predicted means
   - `r_squared()`: Compute R² metric
   - `summarize()`: Compute summary statistics for all models

3. **Plotting**
   - `plot_crps_vs_n()`: Generate CRPS/R² vs training size plots
   - `main()`: Orchestrate all plot generation

## Configuration
Easily customizable variables at the top:
- `TRAIN_CSV`: Training data location
- `CACHE_DIR`: Cached model predictions directory
- `FIGURES_DIR`: Output directory for plots
- Model lists: `MODELS_K_SWEEP`, `MODELS_SIGMA_ABLATION`
- Color and label mappings

## Usage
```bash
python baseline_comparison_cleaned.py
```

The script will:
1. Auto-discover all cached model predictions in CACHE_DIR
2. Load test data and compute metrics
3. Generate all k_component and sigma_ablation plots
4. Save PNG and SVG versions to FIGURES_DIR

## Requirements
- Pre-cached model predictions (.npz files) in `results/baseline_comparison/cache/`
- Test data in `data/original_data.csv` (rows 600+)
- Dependencies: numpy, pandas, matplotlib, scipy

## Output Files
All files are saved to `figures/Baseline_comparison/` with both `.png` and `.svg` versions:
- `crps_vs_n_*_k_components.png/svg`
- `crps_vs_n_*_k_components_inset.png/svg`
- `crps_vs_n_*_sigma_ablation.png/svg`
- `crps_vs_n_*_sigma_ablation_inset.png/svg`
- `r2_vs_n_*_k_components_inset.png/svg`
- `r2_vs_n_*_sigma_ablation_inset.png/svg`

Where `*` is one of: SET, RESET, SET_and_RESET
