r"""
Visualize 2-component Gaussian mixture PDF predictions for one SET and/or
one RESET sample, showing the 5 ensemble-member PDFs, their mean, and the
actual measured value.

Usage:
    python figures/visualize_predictions.py `
      --set-csv predictions/final_predictions_shuffled_model_seperate_states_with_outliers/mdn_predictions_final_models_random_dataset_predictions_with_outliers_shuffled_n125_set.csv 

Usage for comparing the ensemble-mean prediction of several trained models
(datasets) for one sample instead of the 5 shuffle-run members of one model:
    python figures/visualize_predictions.py `
      --compare-models `
        mdn_predictions_train_samples_dev_1_46_600_samples_low_ratio_cleaned_shuffled_n125 `
        mdn_predictions_train_samples_dev_20_21_600_samples_low_ratio_cleaned_shuffled_n125 `
      --state set --sample-idx 180


Usage:
For comparing the ensemble-mean predictions of several trained models for a specific sample, use the --compare-models option as shown above.
python figures/visualize_predictions.py --compare-models `
  "mdn_predictions_final_models_random_dataset_predictions_with_outliers_shuffled_n500" `
  "mdn_predictions_train_samples_dev_50_12_600_samples_high_ratio - Kopie_shuffled_n500" `
  "mdn_predictions_train_samples_dev_28_15_600_samples_high_ratio - Kopie_shuffled_n500" `
  --state set --sample-idx 180

  or run like this for specifying the full path to the prediction files:
  python figures/visualize_predictions.py --compare-models `
  "C:\Users\tbe\preparing-MDN_HfOx\predictions\final_predictions_shuffled_model_seperate_states_with_outliers\mdn_predictions_final_models_random_dataset_predictions_with_outliers_shuffled_n500" `
  "mdn_predictions_train_samples_dev_45_40_600_samples_low_ratio - Kopie_shuffled_n500" `
  --state set --sample-idx 180

  Usage for analysis of the run-to-run variation of mixture components for a specific sample:
    python figures/visualize_predictions.py --seed-variation --state reset

  Usage for analyzing the average deviation of mixture components for a specific sample:
  python figures/visualize_predictions.py --average-deviation
  
  """
import os
import re
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerTuple
from scipy.stats import norm
plt.rcParams.update({
    "font.family": "times new roman",
    "font.size": 14,
    "axes.labelsize": 14,
    "axes.titlesize": 14,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 14,
})
# =========================
# Configuration
# =========================
SET_SAMPLE_IDX = [9]
RESET_SAMPLE_IDX = [1]
OUTPUT_DIR = 'figures/Individual_samples_with_outliers'
MEMBER_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
MEMBER_LINEWIDTH = 1.5
ENSEMBLE_LINEWIDTH = 2
ACTUAL_LINEWIDTH = 2
X_MIN, X_MAX = 0, 150
Y_TICKS = [0.00, 0.06]
FIGURE_SIZE = (3, 3)

DEFAULT_PREDICTIONS_DIR = r'C:\Users\tbe\preparing-MDN_HfOx\predictions\d2d_models_original_data_500'
MODEL_COMPARISON_OUTPUT_DIR = 'figures/Model_comparison'
SEED_VARIATION_PREDICTIONS_DIR = 'predictions/final_predictions_shuffled_model_seperate_states_with_outliers'
SEED_VARIATION_OUTPUT_DIR = 'figures/Seed_variation'
MODEL_COLORS = MEMBER_COLORS


def detect_mixture_columns(df):
    """Detect mixture component columns (pi, mu, sigma for each shuffle run)."""
    shuffle_pi = {}
    shuffle_mu = {}
    shuffle_sigma = {}

    for col in df.columns:
        # Match: shuffle_run1_pi_1, shuffle_run1_pi_2, etc.
        pi_match = re.match(r'^shuffle_run(\d+)_pi_(\d+)$', col)
        mu_match = re.match(r'^shuffle_run(\d+)_mu_(\d+)$', col)
        sigma_match = re.match(r'^shuffle_run(\d+)_sigma_(\d+)$', col)

        if pi_match:
            shuffle_id, comp_id = int(pi_match.group(1)), int(pi_match.group(2))
            shuffle_pi.setdefault(shuffle_id, {})[comp_id] = col
        elif mu_match:
            shuffle_id, comp_id = int(mu_match.group(1)), int(mu_match.group(2))
            shuffle_mu.setdefault(shuffle_id, {})[comp_id] = col
        elif sigma_match:
            shuffle_id, comp_id = int(sigma_match.group(1)), int(sigma_match.group(2))
            shuffle_sigma.setdefault(shuffle_id, {})[comp_id] = col

    return shuffle_pi, shuffle_mu, shuffle_sigma


def get_mixture_components(row, shuffle_id, pi_dict, mu_dict, sigma_dict):
    """Extract mixture components for a specific shuffle run."""
    if shuffle_id not in pi_dict or shuffle_id not in mu_dict or shuffle_id not in sigma_dict:
        return None

    pi_cols = pi_dict[shuffle_id]
    mu_cols = mu_dict[shuffle_id]
    sigma_cols = sigma_dict[shuffle_id]
    n_components = len(pi_cols)

    pi = np.array([row[pi_cols[i + 1]] for i in range(n_components)])
    mu = np.array([row[mu_cols[i + 1]] for i in range(n_components)])
    sigma = np.array([row[sigma_cols[i + 1]] for i in range(n_components)])

    return pi, mu, sigma


def plot_mixture_pdf(ax, y_actual, ensemble_pis, ensemble_mus, ensemble_sigmas, legend_loc='best'):
    """Plot the 5 per-member and the ensemble-averaged 2-component Gaussian mixture PDFs."""
    x = np.linspace(X_MIN, X_MAX, 400)

    # Individual member mixture PDFs: pi_1*N(mu_1,sigma_1) + pi_2*N(mu_2,sigma_2)
    member_lines = []
    for member_idx in range(len(ensemble_pis)):
        pi, mu, sigma = ensemble_pis[member_idx], ensemble_mus[member_idx], ensemble_sigmas[member_idx]
        pdf = pi[0] * norm.pdf(x, mu[0], sigma[0]) + pi[1] * norm.pdf(x, mu[1], sigma[1])
        line, = ax.plot(x, pdf, color=MEMBER_COLORS[member_idx], alpha=0.6, linewidth=MEMBER_LINEWIDTH)
        member_lines.append(line)

    # Ensemble mixture: average of all member PDFs
    ensemble_pdf = np.zeros_like(x)
    for member_idx in range(len(ensemble_pis)):
        pi, mu, sigma = ensemble_pis[member_idx], ensemble_mus[member_idx], ensemble_sigmas[member_idx]
        ensemble_pdf += pi[0] * norm.pdf(x, mu[0], sigma[0]) + pi[1] * norm.pdf(x, mu[1], sigma[1])
    ensemble_pdf /= len(ensemble_pis)

    ax.plot(x, ensemble_pdf, 'k-', linewidth=ENSEMBLE_LINEWIDTH, label='Mean', zorder=10)
    ax.axvline(y_actual, color='red', linestyle='--', linewidth=ACTUAL_LINEWIDTH,
               label=f'GT: {y_actual:.2f} \u00b5S', zorder=5)
    ax.fill_between(x, 0, ensemble_pdf, alpha=0.05, color='black', zorder=1)

    ax.set_xlabel('Conductance [\u00b5S]')
    ax.set_ylabel('PDF')
    ax.set_xlim(X_MIN, X_MAX)
    #ax.grid(True, alpha=0.3)

    # One "Run 1-N" entry with all member lines drawn on top of each other
    handles, labels = ax.get_legend_handles_labels()
    handles.insert(0, tuple(member_lines))
    labels.insert(0, f'Run 1-{len(member_lines)}')
    ax.legend(handles, labels, loc=legend_loc,
              handler_map={tuple: HandlerTuple(ndivide=None, pad=0)})


def _resolve_dataset_csv(predictions_dir, model_name, state):
    """Resolve a dataset/model name (with or without a trailing _set/_reset) to its CSV path."""
    state = state.lower()
    if state not in ('set', 'reset'):
        raise ValueError(f"state must be 'set' or 'reset', got '{state}'")

    base = model_name
    if base.endswith('.csv'):
        base = base[:-len('.csv')]
    for suffix in ('_set', '_reset'):
        if base.endswith(suffix):
            base = base[:-len(suffix)]
            break

    csv_path = os.path.join(predictions_dir, f"{base}_{state}.csv")
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Could not find predictions file: {csv_path}")
    return csv_path


def compute_ensemble_mean_pdf(df, sample_idx, x):
    """
    Compute the ensemble-mean mixture PDF (averaged across all shuffle-run members)
    for a single sample row, along with its ground-truth measured value.

    Returns (pdf_mean, y_actual), or (None, None) if the sample or mixture columns
    are not found.
    """
    pi_dict, mu_dict, sigma_dict = detect_mixture_columns(df)
    if not pi_dict:
        return None, None

    sample_rows = df[df['sample_idx'] == sample_idx]
    if len(sample_rows) == 0:
        return None, None
    row = sample_rows.iloc[0]

    shuffle_ids = sorted(pi_dict.keys())
    pdf_sum = np.zeros_like(x)
    n_valid = 0
    for shuffle_id in shuffle_ids:
        components = get_mixture_components(row, shuffle_id, pi_dict, mu_dict, sigma_dict)
        if components is None:
            continue
        pi, mu, sigma = components
        pdf_sum += pi[0] * norm.pdf(x, mu[0], sigma[0]) + pi[1] * norm.pdf(x, mu[1], sigma[1])
        n_valid += 1

    if n_valid == 0:
        return None, None

    target_col = 'y_true_uS' if 'y_true_uS' in df.columns else 'y_measured_uS'
    return pdf_sum / n_valid, row[target_col]


def plot_model_comparison(model_names, sample_idx, state, predictions_dir=DEFAULT_PREDICTIONS_DIR,
                           output_dir=MODEL_COMPARISON_OUTPUT_DIR,                            legend_loc='best'):
    """
    Overlay the ensemble-mean mixture PDF (one curve per model/dataset, instead of per
    shuffle-run member) for a single sample, to compare predictions across different
    trained models ("Model 1", "Model 2", ...).

    Parameters
    ----------
    model_names : list of str
        Dataset/model base names (the trailing _set/_reset suffix is optional and
        resolved automatically from `state`), e.g.
        'mdn_predictions_train_samples_dev_1_46_600_samples_low_ratio_cleaned_shuffled_n125'.
    sample_idx : int
        The `sample_idx` value (as written by predictions_for_testset.py) to compare.
    state : str
        'set' or 'reset' — selects which of each model's prediction files to load.
    """
    if len(model_names) > len(MODEL_COLORS):
        raise ValueError(f"Can only compare up to {len(MODEL_COLORS)} models at once (got {len(model_names)}).")

    x = np.linspace(X_MIN, X_MAX, 400)
    fig, ax = plt.subplots(1, 1, figsize=FIGURE_SIZE)

    y_actual = None
    for i, model_name in enumerate(model_names):
        csv_path = _resolve_dataset_csv(predictions_dir, model_name, state)
        df = pd.read_csv(csv_path, encoding='utf-8-sig')

        pdf_mean, y_actual_i = compute_ensemble_mean_pdf(df, sample_idx, x)
        if pdf_mean is None:
            print(f"ERROR: Sample {sample_idx} (or mixture columns) not found in {csv_path}, skipping.")
            continue
        if y_actual is None:
            y_actual = y_actual_i

        ax.plot(x, pdf_mean, color=MODEL_COLORS[i], linewidth=ENSEMBLE_LINEWIDTH, label=f'Model {i + 1}')

    if y_actual is not None:
        ax.axvline(y_actual, color='red', linestyle='--', linewidth=ACTUAL_LINEWIDTH,
                   label=f'GT: {y_actual:.2f} \u00b5S', zorder=5)

    ax.set_xlabel('Conductance [\u00b5S]')
    ax.set_ylabel('PDF')
    ax.set_xlim(X_MIN, X_MAX)
    #ax.grid(True, alpha=0.3)
    ax.legend(loc=legend_loc)
    ax.set_box_aspect(1)
    ax.set_yticks(Y_TICKS)
    ax.spines['left'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.yaxis.set_label_position('left')
    ax.yaxis.set_ticks_position('left')

    os.makedirs(output_dir, exist_ok=True)
    filename = f"model_comparison_sample{sample_idx:04d}_{state.upper()}_{len(model_names)}models.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=100, bbox_inches='tight')
    plt.savefig(filepath.replace('.png', '.svg'), bbox_inches='tight')
    plt.close()
    print(f"[OK] Saved: {filepath}")
    print(f"[OK] Saved: {filepath.replace('.png', '.svg')}")
    return filepath


def _plot_and_save_sample(df, sample_idx, state_label, legend_loc, shuffle_ids, pi_dict, mu_dict, sigma_dict,
                           target_col, output_dir, csv_path):
    """Extract mixture components for one sample and save its PDF plot (png + svg)."""
    sample_rows = df[df['sample_idx'] == sample_idx]
    if len(sample_rows) == 0:
        print(f"ERROR: Sample {sample_idx} not found in {state_label} CSV")
        return
    row = sample_rows.iloc[0]

    ensemble_pis, ensemble_mus, ensemble_sigmas = [], [], []
    for shuffle_id in shuffle_ids:
        components = get_mixture_components(row, shuffle_id, pi_dict, mu_dict, sigma_dict)
        if components is not None:
            pi, mu, sigma = components
            ensemble_pis.append(pi)
            ensemble_mus.append(mu)
            ensemble_sigmas.append(sigma)

    print(f"Generating plot for {state_label} sample {sample_idx}...")
    fig, ax = plt.subplots(1, 1, figsize=FIGURE_SIZE)
    plot_mixture_pdf(ax, row[target_col], np.array(ensemble_pis), np.array(ensemble_mus), np.array(ensemble_sigmas),
                      legend_loc=legend_loc)
    ax.set_box_aspect(1)
    ax.set_yticks(Y_TICKS)
    ax.spines['left'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.yaxis.set_label_position('left')
    ax.yaxis.set_ticks_position('left')

    csv_stem = os.path.splitext(os.path.basename(csv_path))[0]
    filename = f"{csv_stem}_sample{int(row['sample_idx']):04d}_{state_label}_v{row['voltage']:.3f}.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=100, bbox_inches='tight')
    plt.savefig(filepath.replace('.png', '.svg'), bbox_inches='tight')
    plt.close()
    print(f"  [OK] Saved: {filepath}")
    print(f"  [OK] Saved: {filepath.replace('.png', '.svg')}")


def resolve_sample_ids(state, override=None):
    """Sample indices to plot for a state: the --sample-idx override or the configured SET/RESET list."""
    if override:
        return list(override)
    return list(SET_SAMPLE_IDX if state == 'set' else RESET_SAMPLE_IDX)


def plot_specific_samples(set_csv=None, reset_csv=None, set_sample_idx=None, reset_sample_idx=None,
                           output_dir=OUTPUT_DIR):
    """Create individual mixture-PDF plots for the SET and/or RESET sample(s) of the CSVs that are given."""
    set_sample_ids = resolve_sample_ids('set', set_sample_idx) if set_csv else []
    reset_sample_ids = resolve_sample_ids('reset', reset_sample_idx) if reset_csv else []
    print(f"Loading data to find sample(s) {set_sample_ids} (SET) and {reset_sample_ids} (RESET)...")

    df_set = pd.read_csv(set_csv, encoding='utf-8-sig') if set_csv else None
    df_reset = pd.read_csv(reset_csv, encoding='utf-8-sig') if reset_csv else None
    df = pd.concat([d for d in (df_set, df_reset) if d is not None], ignore_index=True)
    target_col = 'y_true_uS' if 'y_true_uS' in df.columns else 'y_measured_uS'

    pi_dict, mu_dict, sigma_dict = detect_mixture_columns(df)
    if not pi_dict or not mu_dict or not sigma_dict:
        print("ERROR: No mixture component columns found")
        return
    shuffle_ids = sorted(pi_dict.keys())

    os.makedirs(output_dir, exist_ok=True)

    for sample_idx in set_sample_ids:
        _plot_and_save_sample(df_set, sample_idx, 'SET', 'best', shuffle_ids, pi_dict, mu_dict, sigma_dict,
                              target_col, output_dir, set_csv)
    for sample_idx in reset_sample_ids:
        _plot_and_save_sample(df_reset, sample_idx, 'RESET', 'best', shuffle_ids, pi_dict, mu_dict,
                              sigma_dict, target_col, output_dir, reset_csv)

    print(f"\n[OK] Specific sample plots saved to: {output_dir}")


def collect_seed_variation(predictions_dir, sample_idx, state='set'):
    """Gather per-run mu and pi (components sorted by mu) of one sample for every n-training-samples model.

    Returns {n_train: {'mu': array(runs, 2), 'pi': array(runs, 2)}} sorted by n_train.
    Component 1 is the one with the lower mu in each run.
    """
    file_re = re.compile(rf'_n(\d+)_{state}\.csv$', re.IGNORECASE)
    files = sorted(((int(m.group(1)), fn) for fn in os.listdir(predictions_dir)
                    if (m := file_re.search(fn))))
    if not files:
        raise FileNotFoundError(f"No '*_n<N>_{state}.csv' files in {predictions_dir}")

    results = {}
    for n_train, fn in files:
        df = pd.read_csv(os.path.join(predictions_dir, fn), encoding='utf-8-sig')
        rows = df[df['sample_idx'] == sample_idx]
        if rows.empty:
            print(f"  [WARN] sample {sample_idx} not found in {fn}")
            continue
        row = rows.iloc[0]
        pi_dict, mu_dict, sigma_dict = detect_mixture_columns(df)
        mus, pis = [], []
        for shuffle_id in sorted(pi_dict):
            components = get_mixture_components(row, shuffle_id, pi_dict, mu_dict, sigma_dict)
            if components is None:
                continue
            pi, mu, _ = components
            order = np.argsort(mu)
            mus.append(mu[order])
            pis.append(pi[order])
        results[n_train] = {'mu': np.array(mus), 'pi': np.array(pis)}
    return results


def plot_seed_variation(predictions_dir, sample_idx, state='set', output_dir=SEED_VARIATION_OUTPUT_DIR):
    """Plot the run-to-run (seed) variation of mu and pi vs. number of training samples for one sample.

    Shows scatter points and confidence bands (no mean line to avoid visual bias).
    Includes a separate subplot showing Coefficient of Variation (convergence metric).
    """
    results = collect_seed_variation(predictions_dir, sample_idx, state)
    n_values = np.array(sorted(results))
    os.makedirs(output_dir, exist_ok=True)

    quantities = [
        ('mu', 'Predicted mu (uS)', 'mu'),
        ('pi', 'Predicted p', 'p'),
    ]
    comp_colors = ['#1f77b4', '#d62728']
    saved = []

    for key, ylabel, short in quantities:
        symbol = r'\mu' if key == 'mu' else 'p'
        comp_names = [rf'${symbol}_1$', rf'${symbol}_2$']
        
        # Create figure with 2 subplots: top=data, bottom=CV
        fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(4, 6), 
                                                  gridspec_kw={'height_ratios': [1.5, 1]})
        
        # ===== TOP SUBPLOT: Scatter + Bands (no mean line) =====
        for comp in range(2):
            color = comp_colors[comp]
            means = np.array([results[n][key][:, comp].mean() for n in n_values])
            stds = np.array([results[n][key][:, comp].std(ddof=1) if len(results[n][key]) > 1 else 0.0
                             for n in n_values])
            
            # Scatter points (no mean line)
            for n in n_values:
                vals = results[n][key][:, comp]
                ax_top.scatter(np.full(len(vals), n), vals, s=12, color=color, alpha=0.5, linewidths=0)
            
            # Confidence bands only (±1 std)
            ax_top.fill_between(n_values, means - stds, means + stds, color=color, alpha=0.2, linewidth=0,
                               label=f'{comp_names[comp]}')

        ax_top.set_xscale('log')
        ax_top.set_ylabel(ylabel)
        ax_top.set_ylim(0, 150 if key == 'mu' else 1)
        ax_top.grid(True, alpha=0.3)
        ax_top.legend(loc='best')
        ax_top.set_xticklabels([])  # Hide x labels on top subplot
        
        # ===== BOTTOM SUBPLOT: Coefficient of Variation =====
        for comp in range(2):
            color = comp_colors[comp]
            cvs = []
            
            for n in n_values:
                vals = results[n][key][:, comp]
                mean_val = vals.mean()
                std_val = vals.std(ddof=1) if len(vals) > 1 else 0.0
                # CV = std / mean (avoid division by zero)
                cv = std_val / (np.abs(mean_val) + 1e-6)
                cvs.append(cv)
            
            cvs = np.array(cvs)
            ax_bottom.plot(n_values, cvs, 'o-', color=color, linewidth=2, markersize=5,
                          label=f'{comp_names[comp]}')
        
        # Add vertical line at n=125 to highlight convergence threshold
        ax_bottom.axvline(125, color='gray', linestyle='--', linewidth=1.5, alpha=0.5, label='Convergence threshold')
        
        ax_bottom.set_xscale('log')
        ax_bottom.set_xlabel('Training Samples')
        ax_bottom.set_ylabel('Coefficient of Variation')
        ax_bottom.set_ylim(0, ax_bottom.get_ylim()[1])  # Start at 0
        ax_bottom.grid(True, alpha=0.3)
        ax_bottom.legend(loc='best', fontsize=10)
        
        plt.tight_layout()
        
        filepath = os.path.join(output_dir, f"seed_variation_{short}_sample{sample_idx:04d}_{state.upper()}.png")
        fig.savefig(filepath, dpi=100, bbox_inches='tight')
        fig.savefig(filepath.replace('.png', '.svg'), bbox_inches='tight')
        plt.close(fig)
        saved.append(filepath)
        print(f"[OK] Saved: {filepath}")
    return saved


def _load_sorted_run_means(path):
    """Return a DataFrame indexed by sample_idx with run-mean mu_lo, mu_hi, pi_lo, pi_hi.

    Within each run the two components are ordered by mu (lo = smaller mu) before averaging over runs.
    """
    df = pd.read_csv(path, encoding='utf-8-sig')
    pi_dict, mu_dict, _ = detect_mixture_columns(df)
    runs = sorted(set(pi_dict) & set(mu_dict))
    mu = np.stack([df[[mu_dict[r][1], mu_dict[r][2]]].to_numpy(float) for r in runs])  # (runs, samples, 2)
    pi = np.stack([df[[pi_dict[r][1], pi_dict[r][2]]].to_numpy(float) for r in runs])
    order = np.argsort(mu, axis=2)
    mu = np.take_along_axis(mu, order, axis=2)
    pi = np.take_along_axis(pi, order, axis=2)
    mu_mean, pi_mean = mu.mean(axis=0), pi.mean(axis=0)
    return pd.DataFrame({'mu_lo': mu_mean[:, 0], 'mu_hi': mu_mean[:, 1],
                         'pi_lo': pi_mean[:, 0], 'pi_hi': pi_mean[:, 1]},
                        index=pd.Index(df['sample_idx'].to_numpy(), name='sample_idx'))


def _compute_average_deviation(predictions_dir, states):
    """Return (n_values, n_ref, mean_dev, std_dev) of run-mean mu/pi vs. the largest-n model.

    For every sample the deviation is |run-mean(n) - run-mean(n_max)|; mean and std are taken over the
    samples of all given states pooled together.
    """
    n_values, n_ref = None, None
    pooled = {}
    for state in states:
        file_re = re.compile(rf'_n(\d+)_{state}\.csv$', re.IGNORECASE)
        files = sorted((int(m.group(1)), fn) for fn in os.listdir(predictions_dir) if (m := file_re.search(fn)))
        if len(files) < 2:
            raise FileNotFoundError(f"Need at least two '*_n<N>_{state}.csv' files in {predictions_dir}")

        means = {n: _load_sorted_run_means(os.path.join(predictions_dir, fn)) for n, fn in files}
        state_n_ref = files[-1][0]
        state_n_values = [n for n, _ in files if n != state_n_ref]
        if n_values is None:
            n_values, n_ref = state_n_values, state_n_ref
        elif (state_n_values, state_n_ref) != (n_values, n_ref):
            raise ValueError("SET and RESET files must cover the same training-set sizes to be pooled")

        ref = means[state_n_ref]
        for n in state_n_values:
            common = means[n].index.intersection(ref.index)
            pooled.setdefault(n, []).append((means[n].loc[common] - ref.loc[common]).abs())

    deviations, deviation_stds = {}, {}
    for n in n_values:
        diff = pd.concat(pooled[n], ignore_index=True)
        deviations[n] = diff.mean()
        deviation_stds[n] = diff.std(ddof=1)
    return n_values, n_ref, deviations, deviation_stds


def plot_average_deviation(predictions_dir, states, output_dir=SEED_VARIATION_OUTPUT_DIR):
    """Plot how far the run-averaged mu / pi at each training-set size is from the largest-n model.

    `states` is a state name ('set'/'reset') or a tuple of them; several states are pooled into one curve.
    The curve approaching 0 shows where adding training data stops changing the prediction.
    """
    states = (states,) if isinstance(states, str) else tuple(states)
    tag = '_and_'.join(s.upper() for s in states)
    n_values, n_ref, deviations, deviation_stds = _compute_average_deviation(predictions_dir, states)
    os.makedirs(output_dir, exist_ok=True)
    plots = [('mu', 'Average deviation of \u03bc (\u00b5S)'), ('pi', 'Average deviation of $p$')]
    comp_colors = ['#1f77b4', '#d62728']
    comp_names = [r'$\mu_1$', r'$\mu_2$']
    saved = []
    for key, ylabel in plots:
        fig, ax = plt.subplots(1, 1, figsize=(5, 4))
        # pi_lo + pi_hi = 1, so both components have identical absolute deviations: draw one curve
        components = [(1, 'hi', '$p$ (both components)', 'k')] if key == 'pi' else [
            (0, 'lo', comp_names[0], comp_colors[0]), (1, 'hi', comp_names[1], comp_colors[1])]
        for _, suffix, label, color in components:
            mean = np.array([deviations[n][f'{key}_{suffix}'] for n in n_values])
            std = np.array([deviation_stds[n][f'{key}_{suffix}'] for n in n_values])
            ax.plot(n_values, mean, 'o-', markersize=4, color=color, linewidth=1.5, label=label)
            ax.fill_between(n_values, np.maximum(mean - std, 0), mean + std, color=color, alpha=0.2, linewidth=0)
        ax.set_xscale('log')
        ax.set_xlabel('Training Samples')
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, 150 if key == 'mu' else 1)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        filepath = os.path.join(output_dir, f"average_deviation_{key}_{tag}_ref_n{n_ref}.png")
        fig.savefig(filepath, dpi=100, bbox_inches='tight')
        fig.savefig(filepath.replace('.png', '.svg'), bbox_inches='tight')
        plt.close(fig)
        saved.append(filepath)
        print(f"[OK] Saved: {filepath}")
    return saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize mixture PDF predictions for one SET and one RESET sample")
    parser.add_argument('--set-csv', type=str, default=None, help='Path to SET predictions CSV')
    parser.add_argument('--reset-csv', type=str, default=None, help='Path to RESET predictions CSV (optional)')
    parser.add_argument('--compare-models', type=str, nargs='+', default=None,
                        help="Dataset/model base names (up to 5) to compare via their ensemble-mean PDF, "
                             "e.g. mdn_predictions_train_samples_dev_1_46_600_samples_low_ratio_cleaned_shuffled_n125")
    parser.add_argument('--sample-idx', type=int, nargs='+', default=None,
                        help='One or more sample_idx values (default: SET_SAMPLE_IDX/RESET_SAMPLE_IDX based on --state)')
    parser.add_argument('--state', type=str, choices=['set', 'reset'], default=None,
                        help="State to run: used by --compare-models and --seed-variation (default: set) and to "
                             "restrict the individual-sample plots to SET or RESET (default: every CSV given)")
    parser.add_argument('--predictions-dir', type=str, default=DEFAULT_PREDICTIONS_DIR,
                        help=f'Directory containing model prediction CSVs (default: {DEFAULT_PREDICTIONS_DIR})')
    parser.add_argument('--output-dir', type=str, default=MODEL_COMPARISON_OUTPUT_DIR,
                        help=f'Output directory for --compare-models plots (default: {MODEL_COMPARISON_OUTPUT_DIR})')
    parser.add_argument('--seed-variation', action='store_true',
                        help='Plot run-to-run variation of mu and pi vs. number of training samples '
                             '(all *_n<N>_set.csv files in --seed-variation-dir) for --sample-idx')
    parser.add_argument('--seed-variation-dir', type=str, default=SEED_VARIATION_PREDICTIONS_DIR,
                        help=f'Directory with the *_n<N>_set.csv files (default: {SEED_VARIATION_PREDICTIONS_DIR})')
    parser.add_argument('--average-deviation', action='store_true',
                        help='Plot the average (over all samples) deviation of mu and pi from the largest-n model '
                             'vs. number of training samples, for SET and RESET')
    args = parser.parse_args()

    if args.average_deviation:
        for state in ('set', 'reset'):
            plot_average_deviation(args.seed_variation_dir, state)
        plot_average_deviation(args.seed_variation_dir, ('set', 'reset'))
    elif args.seed_variation:
        state = args.state or 'set'
        for sample_idx in resolve_sample_ids(state, args.sample_idx):
            plot_seed_variation(args.seed_variation_dir, sample_idx, state)
    elif args.compare_models:
        state = args.state or 'set'
        for sample_idx in resolve_sample_ids(state, args.sample_idx):
            plot_model_comparison(args.compare_models, sample_idx, state,
                                   predictions_dir=args.predictions_dir, output_dir=args.output_dir)
    else:
        set_csv = args.set_csv if args.state in (None, 'set') else None
        reset_csv = args.reset_csv if args.state in (None, 'reset') else None
        if not (set_csv or reset_csv):
            parser.error('--set-csv / --reset-csv (matching --state) is required unless --compare-models is used')
        plot_specific_samples(set_csv, reset_csv, args.sample_idx if set_csv else None,
                              args.sample_idx if reset_csv else None)


