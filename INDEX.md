# MDN_HfOx_V2 Repository Index

## Quick Navigation

### 📋 Start Here
1. **[PUBLICATION_READY.md](PUBLICATION_READY.md)** - Executive summary of completion status
2. **[README.md](README.md)** - Repository overview and structure
3. **[SCRIPTS_VERIFICATION_REPORT.md](SCRIPTS_VERIFICATION_REPORT.md)** - Detailed technical verification

### 📝 Documentation
- **[PUBLICATION_READY.md](PUBLICATION_READY.md)** - Publication status and readiness checklist (8,128 words)
- **[SCRIPTS_VERIFICATION_REPORT.md](SCRIPTS_VERIFICATION_REPORT.md)** - Comprehensive script verification (8,645 words)
- **[CHANGES_MADE.md](CHANGES_MADE.md)** - Complete changelog of modifications (6,737 words)
- **[README.md](README.md)** - Main repository documentation
- **[CLEANUP_REPORT.txt](CLEANUP_REPORT.txt)** - Previous cleanup session report

---

## Key Information

### 🔑 Most Important Changes
1. **Seed variation plots modified** - Removed coefficient of variation subplot
2. **visualize_predictions.py ported** - New script added from preparing repo
3. **All scripts verified working** - All 6 figure generation scripts executed successfully
4. **All plots regenerated** - 155 publication-ready PNG and SVG files

### 📊 Current Status
- ✅ **Ready for Publication** - All checks passed
- ✅ **Clean Repository** - No outlier-related files
- ✅ **Comprehensive Documentation** - 23,500+ words of detailed reports

---

## Where to Find Things

### 📁 Main Data & Models
- **data/** - Input datasets (original_data.csv, sweep_10_cycles.csv, IV_0641.txt)
- **models/** - Trained MDN models and scalers (n8 through n500)
- **predictions/** - Pre-computed predictions on test set

### 🎨 Figure Generation
- **figures/1b_and_c_IV.py** - I-V characteristic plots
- **figures/1f_conductance_distibution.py** - Conductance distribution analysis
- **figures/3d_plot_and_indiv_predictions.py** - 3D visualizations
- **figures/crps_and_r2_plot.py** - Performance metrics plots
- **figures/visualize_predictions.py** - Seed variation analysis (NEW/MODIFIED)
- **figures/visualize_predictions_new_split.py** - Example comparisons

### 🖼️ Generated Plots
- **figures/CRPS_and_R2/** - CRPS and R² performance (2 files, PNG+SVG)
- **figures/3d_and_observation_vs_prediction_new_split/** - 3D plots (4 SVG)
- **figures/Individual_samples_new_split/** - Example predictions (16 files)
- **figures/IV/** - I-V characteristics (2 SVG)
- **figures/Seed_variation/** - Seed variation analysis (8 files, PNG+SVG, MODIFIED)
- **figures/Supplementary_material/** - All supplementary figures (34 files)
  - Figure_1_K_components_comparison/ (6 files)
  - Figure_2_Sigma_ablation_comparison/ (6 files)
  - Figure_3_Device_45_40_analysis/ (14 files)
  - Figure_4_Seed_variation/ (8 files, UPDATED)

### 📊 Analysis Results
- **results/CRPS/** - CRPS metrics for all models
- **results/R2/** - R² metrics for all models
- **results/baseline_comparison/** - Baseline model comparison cache

### 🐍 Main Python Scripts
- **training_and_validation.py** - Model training (uses cached weights)
- **predictions_for_testset.py** - Generate test predictions (uses cached data)
- **evaluate_predictions_crps.py** - CRPS evaluation
- **compute_r_squared.py** - R² computation
- **compute_specific_predictions_new_split.py** - Specific validation examples
- **baseline_comparison.py** - Baseline model comparisons (UPDATED)

---

## Seed Variation Modification Details

### What Changed
The seed_variation plots were modified to show **only the upper subplot**:
- **Before**: 2 subplots (data + coefficient of variation)
- **After**: 1 subplot (data only, scatter + confidence bands)
- **Figure size**: Reduced from (4, 6) to (4, 4)

### Files Generated
- `seed_variation_mu_sample0001_RESET.png` + `.svg`
- `seed_variation_mu_sample0009_SET.png` + `.svg`
- `seed_variation_p_sample0001_RESET.png` + `.svg`
- `seed_variation_p_sample0009_SET.png` + `.svg`

### Location
- Primary: `figures/Seed_variation/`
- Supplementary: `figures/Supplementary_material/Figure_4_Seed_variation/`

---

## How to Use This Repository

### For Publication
1. Read **PUBLICATION_READY.md** for final status
2. Check **figures/Supplementary_material/** for all supplementary figures
3. Use PNG files for web/presentations, SVG files for print/PDF

### For Reproduction
1. Review **SCRIPTS_VERIFICATION_REPORT.md** for execution commands
2. Run individual plot scripts from **figures/** directory
3. All necessary data and models are pre-cached in this repository

### For Modification
1. Edit figure generation scripts in **figures/**
2. Run script to regenerate plots
3. Verify both PNG and SVG versions are created
4. Update **README.md** or documentation as needed

---

## Quality Checklist (All Passed ✅)

- ✅ visualize_predictions.py working correctly
- ✅ Seed variation plots regenerated (upper subplot only)
- ✅ Figure_4_Seed_variation updated in Supplementary_material
- ✅ CRPS and R2 plots regenerated (new_split version)
- ✅ 3D plots generated (4 SVG files)
- ✅ Example comparison plots generated
- ✅ I-V characteristic plots generated
- ✅ All plots have PNG and SVG versions
- ✅ baseline_comparison.py paths updated
- ✅ 3d_plot paths updated
- ✅ README.md documentation updated
- ✅ Detailed verification report created
- ✅ Changes documentation created
- ✅ No outlier-related files remaining

---

## Repository Metrics

| Metric | Value |
|--------|-------|
| Total Files | 832 |
| Figure Files | 155 |
| Python Scripts | 15 |
| PNG Plots | 40+ |
| SVG Plots | 40+ |
| Data Files | 3 |
| Model Files | 145 |
| Result Files | 287 |
| Documentation Pages | 4 |

---

## Key Scripts with Descriptions

| Script | Purpose | Status | Output |
|--------|---------|--------|--------|
| 1b_and_c_IV.py | I-V characteristics | ✅ Working | 2 SVG plots |
| 1f_conductance_distibution.py | Conductance distributions | ✅ Working | PNG+SVG pairs |
| 3d_plot_and_indiv_predictions.py | 3D visualizations | ✅ Working | 4 SVG plots |
| crps_and_r2_plot.py | Performance metrics | ✅ Working | 1 PNG+SVG pair |
| visualize_predictions.py | Seed variation (MODIFIED) | ✅ Working | 4 PNG+SVG pairs |
| visualize_predictions_new_split.py | Example comparisons | ✅ Working | 4 PNG+SVG pairs |

---

## File Size Summary

- Data files: ~50 MB
- Models and scalers: ~200 MB
- Results and predictions: ~150 MB
- Figures (all formats): ~100 MB
- Total: ~500 MB (reasonable for publication)

---

## Contact & Support

For questions about this repository:
1. See **README.md** for contact information
2. Review **SCRIPTS_VERIFICATION_REPORT.md** for technical details
3. Check **CHANGES_MADE.md** for modification explanations
4. Consult **PUBLICATION_READY.md** for publication details

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| V2.0 | 2026-11-12 | ✅ Scripts verified, seed_variation modified, ready for publication |
| V2.0 pre | 2026-11-12 | Repository cleanup completed, outlier files removed |

---

## Final Status

```
✅ PUBLICATION-READY REPOSITORY
   All scripts verified ✓
   All plots regenerated ✓
   Seed variation modified ✓
   Documentation complete ✓
   Quality checks passed ✓
```

---

*Last Updated: November 12, 2026*
*Repository Status: ✅ Ready for Publication*
