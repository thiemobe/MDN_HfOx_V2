# Baseline Comparison Script - Final Version

## Summary
Cleaned and corrected the `baseline_comparison_cleaned.py` script to generate ONLY the plots needed for supplementary material:
1. **K-component comparison plots** (K=1..5)
2. **Sigma ablation with QR inset plots** (MDN2, mixshared, quantile)

## Important Fix
**Fixed CRPS calculation bug**: The initial version used an incorrect CRPS formula. Now uses the correct closed-form formula with `ndtr` from scipy.special, exactly matching the original `baseline_comparison.py`.

## Generated Plots (30 total files)

### K-Component Comparison
- `crps_vs_n_SET_k_components.png/svg` - CRPS vs training size for SET
- `crps_vs_n_RESET_k_components.png/svg` - CRPS vs training size for RESET
- `crps_vs_n_SET_and_RESET_k_components.png/svg` - CRPS vs training size pooled
- `crps_vs_n_*_k_components_inset.png/svg` - Inset plots (100-500 samples)
- `r2_vs_n_*_k_components_inset.png/svg` - R² inset plots

**Models compared**: K=1 (hetero), K=2 (mdn2), K=3, K=4, K=5

### Sigma Ablation with QR Comparison
- `crps_vs_n_*_sigma_ablation_qr_inset.png/svg` - CRPS comparison (MDN2, mixshared, QNN)
- `r2_vs_n_*_sigma_ablation_qr_inset.png/svg` - R² comparison (MDN2, mixshared, QNN)

**Models compared**: 
- MDN2: 2 Gaussians with learned σ(x)
- mixshared: 2 Gaussians with shared constant σ
- quantile: Quantile regression neural network

## Files
- **Script**: `baseline_comparison_cleaned.py` (322 lines)
- **Output directory**: `figures/Baseline_comparison/`
- **Output formats**: PNG (100 dpi) + SVG (vector)

## Usage
```bash
python baseline_comparison_cleaned.py
```

## Configuration
All customizable at the top of the script:
- `TRAIN_CSV`: Training data path
- `CACHE_DIR`: Cached model predictions directory
- `FIGURES_DIR`: Output directory for plots

## CRPS Formula
Uses closed-form CRPS calculation for Gaussian mixtures:
```
first_term = sum_k(pi_k * (2*sigma_k*pdf(z) + (y - mu_k)*(2*cdf(z) - 1)))
second_term = 0.5 * sum_ij(pi_i*pi_j * |E[|X_i - X_j|]|)
CRPS = first_term - second_term
```

Where:
- `z = (y - mu) / sigma`
- X_i and X_j are samples from mixture components i and j
- Integration is computed in closed form using the normal CDF/PDF

## Plots Features
- **Error bands**: Show standard deviation across 5 training runs
- **Log scale**: Training samples axis uses logarithmic scale
- **Inset plots**: Zoomed to 100-500 training samples
- **Multiple metrics**: Both CRPS (main plot) and R² (inset plots)
- **Clean styling**: Times New Roman font, publication-ready appearance
