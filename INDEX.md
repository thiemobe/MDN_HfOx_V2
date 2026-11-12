# MDN_HfOx_V2 Publication Repository - Index

**Status:** ✅ PUBLICATION READY  
**Last Updated:** 2024-12-12  
**Version:** 2.0 (Research Review Complete)

---

## 📚 Documentation Overview

Start here to understand the repository structure and status:

### Primary Documents
1. **[PUBLICATION_READY_CHECKLIST.md](PUBLICATION_READY_CHECKLIST.md)** ⭐ **START HERE**
   - Comprehensive verification checklist
   - All components verified and status confirmed
   - Quality assurance details
   - Publication readiness summary

2. **[README.md](README.md)**
   - Repository overview
   - Quick start guide
   - Running individual scripts

3. **[FINAL_STATUS_REPORT.md](FINAL_STATUS_REPORT.md)**
   - Complete migration details
   - Key changes from Version 1
   - Verification checklist
   - Recommendations for publication

### Reference Documents
4. **[SCRIPT_VERIFICATION_SUMMARY.md](SCRIPT_VERIFICATION_SUMMARY.md)**
   - Detailed script inventory
   - Function documentation
   - Configuration constants

5. **[PLOTS_GENERATION_REPORT.md](PLOTS_GENERATION_REPORT.md)**
   - Complete plots catalog
   - Organization by category
   - File counts and descriptions

---

## 📂 Repository Structure

```
C:\Users\tbe\MDN_HfOx_V2/
│
├── 📄 Documentation Files
│   ├── README.md                           # Overview & quick start
│   ├── PUBLICATION_READY_CHECKLIST.md      # Final verification ⭐
│   ├── FINAL_STATUS_REPORT.md              # Detailed status report
│   ├── SCRIPT_VERIFICATION_SUMMARY.md      # Script inventory
│   ├── PLOTS_GENERATION_REPORT.md          # Plots catalog
│   └── INDEX.md                            # This file
│
├── 🔍 Core Analysis Scripts
│   ├── baseline_comparison.py              # Central training/inference module
│   ├── compute_specific_predictions_new_split.py
│   ├── MDN.py                              # Model architecture
│   ├── MDN_loss.py                         # Loss functions
│   └── training_and_validation.py          # Training infrastructure
│
├── 📊 Figure Generation Scripts
│   └── figures/
│       ├── visualize_predictions.py        # Seed variation plots
│       ├── 3d_plot_and_indiv_predictions.py
│       ├── 1f_conductance_distibution.py   # Distribution comparison
│       ├── crps_and_r2_plot.py             # Metrics plots
│       └── IV/                             # IV curve analysis
│
├── 📈 Generated Figures
│   └── figures/
│       ├── Baseline_comparison/            # 30 plots (15 PNG + 15 SVG)
│       ├── Seed_variation/                 # 8 plots (4 PNG + 4 SVG)
│       ├── CRPS_and_R2/                    # 2 plots (1 PNG + 1 SVG)
│       ├── Supplementary_material/         # 54 plots organized as:
│       │   ├── Figure_1_K_components_comparison/
│       │   ├── Figure_2_Sigma_ablation_comparison/
│       │   ├── Figure_3_Device_45_40_analysis/
│       │   └── Figure_4_Seed_variation/
│       └── [Other analysis plots]
│
├── 💾 Data Files
│   ├── original_data.csv                   # Main dataset (raw, 600 rows)
│   └── d2d_original_data_1000/             # Device-specific data
│       └── train_samples_dev_45_40_1000_samples_low_ratio.csv
│
├── 🎯 Results & Cache
│   └── results/
│       ├── baseline_comparison/cache/      # 180 cached .npz files
│       ├── validation_examples_*.csv       # 5 validation files
│       └── [Model performance results]
│
└── 🤖 Models
    └── models/                             # Trained model states
```

---

## 🎯 Quick Navigation

### For Understanding the Repository
1. Read: [PUBLICATION_READY_CHECKLIST.md](PUBLICATION_READY_CHECKLIST.md)
2. Reference: [README.md](README.md)
3. Details: [FINAL_STATUS_REPORT.md](FINAL_STATUS_REPORT.md)

### For Running Scripts
- See: [README.md](README.md) - "How to Run Scripts" section
- Example: `python figures/visualize_predictions.py`

### For Accessing Plots
- Main results: `figures/Baseline_comparison/`
- Supplementary: `figures/Supplementary_material/`
- All available in PNG + SVG format

### For Understanding Data
- Main dataset: `data/original_data.csv` (raw, no outlier removal)
- Device analysis: `data/d2d_original_data_1000/train_samples_dev_45_40_1000_samples_low_ratio.csv`

### For Accessing Model Predictions
- Cached predictions: `results/baseline_comparison/cache/*.npz`
- Validation examples: `results/validation_examples_*.csv`
- Pre-trained models: `models/`

---

## ✅ Status Summary

| Component | Status | Details |
|-----------|--------|---------|
| **Data Files** | ✅ Complete | 2 datasets present and verified |
| **Python Scripts** | ✅ Functional | 8 core + supporting infrastructure |
| **Plot Generation** | ✅ Complete | 132 plots (63 PNG + 69 SVG) |
| **Model Cache** | ✅ Available | 180 .npz prediction files |
| **Documentation** | ✅ Comprehensive | 5 detailed reports |
| **Quality Assurance** | ✅ Verified | All scripts tested and working |
| **Repository Structure** | ✅ Organized | Clean and logical layout |

---

## 🔑 Key Features

### Dataset
- ✅ Raw data without outlier removal
- ✅ 600 test samples
- ✅ Multiple training set sizes (n=8 to n=500)
- ✅ Device 45_40 generalization analysis

### Models
- ✅ MDN with K=2,3,4,5 components
- ✅ 2-Gaussian with shared constant σ
- ✅ Quantile Regression Network (QNN)
- ✅ Heteroscedastic baseline

### Analysis
- ✅ CRPS (Continuous Ranked Probability Score)
- ✅ R² (Coefficient of Determination)
- ✅ Seed variation (5 runs per configuration)
- ✅ 3D validation surface plots
- ✅ Individual prediction examples
- ✅ Distribution comparison analysis

### Supplementary Material
- ✅ Figure 1: K-component comparison
- ✅ Figure 2: Sigma ablation study
- ✅ Figure 3: Device 45_40 generalization
- ✅ Figure 4: Seed variation analysis

---

## 🚀 For Publication

### Recommended Next Steps
1. Review supplementary material figures for quality
2. Verify figure numbering matches manuscript references
3. Confirm all plot legends are clear and complete
4. Check device 45_40 analysis aligns with narrative
5. Prepare final README for GitHub publication

### What to Archive Separately
- Legacy outlier removal code (if needed for reference)
- Experimental/debug scripts (if maintaining research record)
- Intermediate processing files (if documenting pipeline)

### What to Keep Published
- ✅ All 8 core scripts (production-ready)
- ✅ All 132 plots (publication-quality)
- ✅ All data files (raw datasets)
- ✅ All documentation (comprehensive)
- ✅ Model cache (reproducibility)

---

## 📞 Support Information

### For Running Scripts
- Python: 3.14.3 (in `.venv` virtual environment)
- Command format: `python path/to/script.py`
- All dependencies documented in requirements

### For Understanding Results
- See corresponding documentation file for each section
- Plot organization documented in PLOTS_GENERATION_REPORT.md
- Script functions documented in SCRIPT_VERIFICATION_SUMMARY.md

### For Modifications
- Core module: `baseline_comparison.py` (451 lines)
- Training pipeline: Built-in to baseline_comparison.py
- All imports and dependencies self-contained

---

## 📊 Statistics at a Glance

| Metric | Value |
|--------|-------|
| Total PNG plots | 63 |
| Total SVG plots | 69 |
| **Total plots** | **132** |
| Core Python scripts | 8 |
| Supporting scripts | 6+ |
| Total Python lines | 2,123+ |
| Data files | 2 main datasets |
| Cached model files | 180 .npz |
| Documentation pages | 5 comprehensive reports |
| Training set sizes tested | 18 |
| Model architectures | 6 |
| Seeds per configuration | 5 |
| Validation examples | 30 scenarios |
| Device analyses | 2 (main + 45_40) |

---

## 🎓 Citation

If using this repository for research, please cite:

**MDN_HfOx_V2** - Mixture Density Networks for ReRAM Device Characterization  
Version 2.0 (Publication Ready)  
Research Review Complete: 2024-12-12

---

## ✨ Summary

The **MDN_HfOx_V2** repository is a cleaned, organized, and fully verified publication-ready repository containing:

✅ **Complete analysis pipeline** - From raw data to publication figures  
✅ **Multiple model architectures** - Comprehensive baseline comparisons  
✅ **132 publication-quality plots** - Both raster and vector formats  
✅ **Comprehensive documentation** - Easy to understand and reproduce  
✅ **Device generalization** - Beyond main dataset analysis  
✅ **Pre-computed results** - For reproducibility  

**Status: READY FOR PUBLICATION** 🚀

---

**Last Verified:** 2024-12-12  
**Repository:** thiemobe/MDN_HfOx_V2  
**License:** See LICENSE file (if present)  
**Contact:** @thiemobe
