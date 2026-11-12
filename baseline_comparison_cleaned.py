r"""
Generate k_component comparison and sigma_ablation_qr_inset plots.

This script loads pre-cached model predictions and generates CRPS/R² plots:
    1. K-component sweep: hetero (K=1), mdn2 (K=2), mdn3 (K=3), mdn4 (K=4), mdn5 (K=5)
    2. Sigma ablation with quantile regression (QR) inset: mdn2, mixshared, quantile

Plots use the same metrics and closed-form CRPS calculation as the original baseline_comparison.py

Configuration (modify if needed):
    TRAIN_CSV: Path to training data file
    CACHE_DIR: Directory containing cached baseline model predictions (*.npz files)
    FIGURES_DIR: Output directory for PNG and SVG plots

Usage:
    python baseline_comparison_cleaned.py
"""

import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
from scipy.special import ndtr

# =========================
# Configuration
# =========================
TRAIN_CSV = 'data/original_data.csv'
N_POOL = 600  # rows 0..599: train + validation pool; rows 600..: test set
MDN_PREDICTIONS_DIR = 'predictions'
CACHE_DIR = 'results/baseline_comparison/cache'
FIGURES_DIR = 'figures/Baseline_comparison'

# Models for component and sigma ablation studies
MODELS_K_SWEEP = ('hetero', 'mdn2', 'mdn3', 'mdn4', 'mdn5')  # K = 1..5
MODELS_QR_COMPARISON = ('mdn2', 'mixshared', 'quantile')  # For qr_inset plots

# Model labels for plots
K_LABELS = {'hetero': 'K=1', 'mdn2': 'K=2', 'mdn3': 'K=3', 'mdn4': 'K=4', 'mdn5': 'K=5'}
QR_LABELS = {
    'mdn2': 'MDN, 2 Gaussians, $\\sigma(x)$',
    'mixshared': '2 Gaussians, shared const. $\\sigma$',
    'quantile': 'Quantile regression NN',
}
MODEL_COLORS = {
    'hetero': '#1f77b4', 'mdn2': '#d62728', 'mdn3': '#ff7f0e', 'mdn4': '#9467bd', 'mdn5': '#8c564b',
    'quantile': '#2ca02c', 'mixshared': '#e377c2'
}

STATES = ('set', 'reset')
N_QUANTILES = 100
TAUS = (np.arange(N_QUANTILES) + 0.5) / N_QUANTILES

plt.rcParams.update({
    "font.family": "times new roman",
    "font.size": 14,
    "axes.labelsize": 14,
    "axes.titlesize": 14,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 12,
})


# =========================
# Data Loading
# =========================
def parse_original_rows(df):
    """Parse raw data rows: extract state, G_before, V, and y=mean(G_after)."""
    state = np.where(df.iloc[:, 0].astype(str).str.strip().str.lower() == 'set', 1.0, 0.0)
    g_before = pd.to_numeric(df.iloc[:, 9], errors='coerce').to_numpy(float) * 1e6
    voltage = pd.to_numeric(df.iloc[:, 3], errors='coerce').to_numpy(float)
    # y = mean of G_after measurements at 1s, 5s, 10s (columns 11, 14, 17)
    y = pd.to_numeric(df.iloc[:, [11, 14, 17]].mean(axis=1), errors='coerce').to_numpy(float) * 1e6
    X = np.column_stack([state, g_before, voltage])
    assert np.all(np.isfinite(X)) and np.all(np.isfinite(y)), "NaNs in data"
    return X, y


def load_test_data():
    """Load test set data (rows 600+) from training CSV."""
    df = pd.read_csv(TRAIN_CSV, encoding='utf-8-sig').iloc[N_POOL:]
    X, y_all = parse_original_rows(df)
    masks = {
        'set': X[:, 0] == 1.0,
        'reset': X[:, 0] == 0.0,
    }
    return X, y_all, masks


def cache_path(kind, n):
    """Path to cached predictions for model kind and training size n."""
    return os.path.join(CACHE_DIR, f'{kind}_n{n}.npz')


# =========================
# Metrics Computation
# =========================
def crps_mixture(y, pi, mu, sigma):
    """
    Closed-form CRPS of Gaussian mixtures (matches original baseline_comparison.py).
    
    Args:
        y: (N,) observed values
        pi: (R, N, C) mixture weights
        mu: (R, N, C) means
        sigma: (R, N, C) standard deviations
    Returns:
        (R, N) CRPS values for each run and sample
    """
    sigma = np.maximum(sigma, 1e-6)
    yy = y[None, :, None]
    z = (yy - mu) / sigma
    # First term: expectation of absolute difference
    first = (pi * (2 * sigma * norm.pdf(z) + (yy - mu) * (2 * ndtr(z) - 1))).sum(-1)
    # Second term: variance-like term from pairwise distances
    d = mu[..., :, None] - mu[..., None, :]
    s = np.sqrt(sigma[..., :, None] ** 2 + sigma[..., None, :] ** 2)
    zz = d / s
    abs_diff = 2 * s * norm.pdf(zz) + d * (2 * ndtr(zz) - 1)
    second = 0.5 * (pi[..., :, None] * pi[..., None, :] * abs_diff).sum((-1, -2))
    return first - second


def crps_quantiles(y, q):
    """CRPS from quantile function."""
    q = np.sort(q, axis=-1)
    diff = y[None, :, None] - q
    return 2.0 * np.maximum(TAUS * diff, (TAUS - 1.0) * diff).mean(-1)


def per_sample_crps(kind, n, state, y_true):
    """CRPS (R, N) of one model for one n and state."""
    data = np.load(cache_path(kind, n))
    if kind == 'quantile':
        return crps_quantiles(y_true, data[f'{state}_q'].astype(float))
    return crps_mixture(y_true, *(data[f'{state}_{k}'].astype(float) for k in ('pi', 'mu', 'sigma')))


def per_sample_mean(kind, n, state):
    """Predicted mean (R, N) in uS of one model for one n and state."""
    data = np.load(cache_path(kind, n))
    if kind == 'quantile':
        return data[f'{state}_q'].astype(float).mean(-1)
    pred = {k: data[f'{state}_{k}'].astype(float) for k in ('pi', 'mu')}
    return (pred['pi'] * pred['mu']).sum(-1)


def r_squared(y_true, y_pred):
    """R² = 1 - SS_res / SS_tot."""
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    return np.nan if ss_tot == 0 else 1 - np.sum((y_true - y_pred) ** 2) / ss_tot


def summarize(n_values, models):
    """Compute CRPS and R² summary statistics for all models."""
    X, y_all, masks = load_test_data()
    y_pooled = np.concatenate([y_all[masks[s]] for s in STATES])
    rows = []
    for n in n_values:
        for kind in models:
            crps = {s: per_sample_crps(kind, n, s, y_all[masks[s]]) for s in STATES}
            pred_means = {s: per_sample_mean(kind, n, s) for s in STATES}
            means = np.concatenate([pred_means[s] for s in STATES], axis=1)
            # R^2 per run (pooled and per-state), then mean/std over runs
            r2_runs = {'SET_and_RESET': np.array([r_squared(y_pooled, run_pred) for run_pred in means])}
            for s in STATES:
                r2_runs[s.upper()] = np.array([r_squared(y_all[masks[s]], p) for p in pred_means[s]])
            groups = {'SET': crps['set'], 'RESET': crps['reset'],
                      'SET_and_RESET': np.concatenate([crps['set'], crps['reset']], axis=1)}
            for tag, values in groups.items():
                run_means = np.nanmean(values, axis=1)
                row = {'model': kind, 'n_train': n, 'state': tag, 'crps_mean': run_means.mean(),
                       'crps_std_over_runs': run_means.std(ddof=1), 'n_test': values.shape[1],
                       'r2_mean': np.nanmean(r2_runs[tag]), 'r2_std_over_runs': np.nanstd(r2_runs[tag])}
                rows.append(row)
    return pd.DataFrame(rows)


# =========================
# Plotting
# =========================
def plot_crps_vs_n(summary, tag, models, output_dir, suffix='', labels=None, metric='crps', 
                   legend_below=True, inset_range=None, inset_rect=(0.5, 0.5, 0.42, 0.42)):
    """
    Plot CRPS or R² vs training set size.
    
    Args:
        summary: DataFrame with summary statistics
        tag: 'SET', 'RESET', or 'SET_and_RESET'
        models: List of model names to plot
        output_dir: Output directory for PNG/SVG
        suffix: Filename suffix (e.g., '_k_components')
        labels: Dict mapping model names to plot labels
        metric: 'crps' or 'r2'
        legend_below: If True, place legend below plot
        inset_range: (lo, hi) for inset plot range
        inset_rect: Inset position (x, y, w, h)
    """
    if labels is None:
        labels = {m: m for m in models}
    
    mean_col, std_col = (('crps_mean', 'crps_std_over_runs') if metric == 'crps'
                         else ('r2_mean', 'r2_std_over_runs'))
    fig, ax = plt.subplots(1, 1, figsize=(3, 3))
    for kind in models:
        d = summary[(summary.model == kind) & (summary.state == tag)].sort_values('n_train')
        color = MODEL_COLORS.get(kind, '#333333')
        ax.plot(d.n_train, d[mean_col], 'o-', markersize=4, color=color, linewidth=1.5, label=labels[kind])
        ax.fill_between(d.n_train, d[mean_col] - d[std_col], d[mean_col] + d[std_col],
                        color=color, alpha=0.15, linewidth=0)
    ax.set_xscale('log')
    ax.set_xlabel('Training Samples')
    ax.set_ylabel('CRPS (\u00b5S)' if metric == 'crps' else '$R^2$')
    ax.grid(True, alpha=0.3)
    
    if inset_range is not None:
        lo, hi = inset_range
        axins = ax.inset_axes(inset_rect)
        ys = []
        for kind in models:
            d = summary[(summary.model == kind) & (summary.state == tag)].sort_values('n_train')
            d = d[(d.n_train >= lo) & (d.n_train <= hi)]
            color = MODEL_COLORS.get(kind, '#333333')
            axins.plot(d.n_train, d[mean_col], 'o-', markersize=2.5, color=color, linewidth=1)
            axins.fill_between(d.n_train, d[mean_col] - d[std_col], d[mean_col] + d[std_col],
                               color=color, alpha=0.15, linewidth=0)
            ys += [(d[mean_col] - d[std_col]).min(), (d[mean_col] + d[std_col]).max()]
        if ys:
            pad = 0.05 * (max(ys) - min(ys))
            axins.set_xscale('log')
            axins.set_xlim(lo * 0.9, hi * 1.1)
            axins.set_ylim(min(ys) - pad, max(ys) + pad)
            axins.set_xticks([lo, hi])
            axins.set_xticklabels([str(lo), str(hi)])
            axins.minorticks_off()
            axins.tick_params(labelsize=8, pad=1)
            axins.grid(True, alpha=0.3)
            ax.indicate_inset_zoom(axins, edgecolor='0.4')
    
    if legend_below:
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.28), frameon=False)
    else:
        ax.legend(loc='best')
    
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f'{metric}_vs_n_{tag}{suffix}.png')
    fig.savefig(path, dpi=100, bbox_inches='tight')
    fig.savefig(path.replace('.png', '.svg'), bbox_inches='tight')
    plt.close(fig)
    print(f"[OK] Saved: {path}")


# =========================
# Main
# =========================
def main():
    """Generate k_component comparison and sigma_ablation_qr_inset plots."""
    # Discover available training set sizes from cached files
    n_values = set()
    for fn in os.listdir(CACHE_DIR):
        m = re.search(r'_n(\d+)\.npz$', fn)
        if m:
            n_values.add(int(m.group(1)))
    n_values = sorted(n_values)
    print(f"Found {len(n_values)} training set sizes: {n_values}")
    
    # Compute summary statistics for all required models
    all_models = list(MODELS_K_SWEEP) + list(MODELS_QR_COMPARISON)
    summary = summarize(n_values, all_models)
    
    # === Generate k_component plots (CRPS and R²) ===
    for tag in ('SET', 'RESET', 'SET_and_RESET'):
        # CRPS main plots
        plot_crps_vs_n(summary, tag, MODELS_K_SWEEP, FIGURES_DIR, suffix='_k_components', 
                      labels=K_LABELS, metric='crps')
        # CRPS inset plots
        plot_crps_vs_n(summary, tag, MODELS_K_SWEEP, FIGURES_DIR, suffix='_k_components_inset',
                      labels=K_LABELS, metric='crps', inset_range=(100, 500))
        # R² inset plots
        plot_crps_vs_n(summary, tag, MODELS_K_SWEEP, FIGURES_DIR, suffix='_k_components_inset',
                      labels=K_LABELS, metric='r2', inset_range=(100, 500), 
                      inset_rect=(0.5, 0.08, 0.42, 0.42))
    
    # === Generate sigma_ablation_qr_inset plots (CRPS and R²) ===
    for tag in ('SET', 'RESET', 'SET_and_RESET'):
        # CRPS qr_inset (MDN2, mixshared, quantile)
        plot_crps_vs_n(summary, tag, MODELS_QR_COMPARISON, FIGURES_DIR,
                      suffix='_sigma_ablation_qr_inset', labels=QR_LABELS,
                      legend_below=True, inset_range=(100, 500))
        # R² qr_inset (MDN2, mixshared, quantile)
        plot_crps_vs_n(summary, tag, MODELS_QR_COMPARISON, FIGURES_DIR,
                      suffix='_sigma_ablation_qr_inset', labels=QR_LABELS, metric='r2',
                      legend_below=True, inset_range=(100, 500),
                      inset_rect=(0.5, 0.08, 0.42, 0.42))
    
    print("\n[OK] All plots generated successfully!")
    print("\nGenerated plots:")
    print("  - K-component comparison: crps_vs_n_*_k_components*.png/svg")
    print("  - Sigma ablation with QR: crps_vs_n_*_sigma_ablation_qr_inset.png/svg")


if __name__ == '__main__':
    main()
