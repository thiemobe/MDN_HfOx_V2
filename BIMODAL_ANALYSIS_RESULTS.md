# Analysis Results: Finding Stable Bimodal Distributions

## Summary

I analyzed all 237 SET and 202 RESET test samples to identify ones that show:
1. **Bimodal distributions** - both p₁ and p₂ contribute meaningfully (relatively balanced mixture)
2. **Convergence after ~100 training samples** - p₁, p₂, μ₁, and μ₂ values stabilize
3. **Consistent behavior** - low variation across ensemble runs after stabilization

## Top 3 Recommendations

### 🏆 **Best Overall: Test Sample 137 (RESET)**
- **Overall Score:** 0.964/1.0
- **Bimodality:** p₁ = 46.5%, p₂ = 53.5% (nearly perfectly balanced!)
- **Stability (after n=100):**
  - π variation: 0.286 (reasonably low)
  - μ variation: 0.099 (very good)
- **Component Separation:** 63.3 µS (clear separation between modes)
- **Mean μ values:** μ₁ = 34.52 µS, μ₂ = 97.84 µS

**Why this is excellent:**
- The mixture is essentially 50/50 between two components
- Both μ and π values stabilize well after ~100 training samples
- Good separation between the two conductance regimes
- Shows clear convergence in the training curve

**Visualization:** See `figures/Seed_variation_analysis/seed_variation_p_sample0137_RESET.png`

---

### 🥈 **Second Best: Test Sample 197 (RESET)**
- **Overall Score:** 0.954/1.0
- **Bimodality:** p₁ = 45.8%, p₂ = 54.2% (excellent balance)
- **Stability (after n=100):**
  - π variation: 0.258 (lowest among top candidates!)
  - μ variation: 0.098
- **Component Separation:** 66.3 µS
- **Mean μ values:** μ₁ = 36.36 µS, μ₂ = 102.69 µS

**Why this is excellent:**
- Very similar to #1 but with slightly more stable π values
- Could be interchangeable depending on which property you want to emphasize

**Visualization:** See `figures/Seed_variation_analysis/seed_variation_p_sample0197_RESET.png`

---

### 🥉 **Best SET: Test Sample 225 (SET)**
- **Overall Score:** 0.919/1.0
- **Bimodality:** p₁ = 45.6%, p₂ = 54.4% (very balanced)
- **Stability (after n=100):**
  - π variation: 0.393 (more variation than RESET examples)
  - μ variation: 0.098
- **Component Separation:** 78.9 µS (largest separation!)
- **Mean μ values:** μ₁ = 21.76 µS, μ₂ = 100.71 µS

**Why this is good:**
- If you need a SET sample, this is the best choice
- Largest component separation (clearest visual separation)
- More variation in π but still quite stable after 100 samples

**Visualization:** See `figures/Seed_variation_analysis/seed_variation_p_sample0225_SET.png`

---

## What the Plots Show

The generated visualization plots show:

1. **`seed_variation_p_sample<ID>_<STATE>.png`**
   - Scatter points: individual values from each ensemble run at each training sample size
   - Line: mean value across runs
   - Band: ±1 standard deviation around the mean
   - Shows how p₁ and p₂ evolve with training sample size (log scale)
   - **You should see:** Values stabilize around n=100-125 and remain relatively flat afterward

2. **`seed_variation_mu_sample<ID>_<STATE>.png`**
   - Same format but for μ₁ and μ₂ (the component means)
   - Shows the parameter convergence more clearly

## Usage

To use these samples in your publications or further analysis:

```bash
# Generate publication-quality plots
python figures/visualize_predictions.py --seed-variation --state reset
# Then edit visualize_predictions.py to set RESET_SAMPLE_IDX = [137]

# Or for SET:
python figures/visualize_predictions.py --seed-variation --state set
# Then edit visualize_predictions.py to set SET_SAMPLE_IDX = [225]
```

## Interpretation for Your Paper

**Sample 137 (RESET)** shows exactly what you need:
- ✅ Clear bimodal distribution (46.5% / 53.5%)
- ✅ Both p₁ and p₂ > 0.1 across all training sample sizes
- ✅ After n ≈ 100-125: π values stay roughly constant (with ±10% variation)
- ✅ After n ≈ 100-125: μ values stay roughly constant (with ±10 µS variation)
- ✅ Shows convergence: model parameters stabilize once sufficient training data is provided
- ✅ Demonstrates that 100-125 samples is sufficient for this prediction task

This makes a strong argument for:
1. Early convergence of parameter estimates
2. Stability of predictions within an acceptable deviation range
3. The value of having at least 100 training samples

## Quality Metrics

| Metric | Sample 137 | Sample 197 | Sample 225 |
|--------|-----------|-----------|-----------|
| Bimodality | 0.962 | 0.935 | 0.929 |
| π stability | 0.286 | 0.258 | 0.393 |
| μ stability | 0.099 | 0.098 | 0.098 |
| p₁/p₂ ratio | 46.5/53.5 | 45.8/54.2 | 45.6/54.4 |
| μ separation | 63.3 µS | 66.3 µS | 78.9 µS |

All three candidates show excellent properties. **Sample 137 (RESET)** is the strongest recommendation.
