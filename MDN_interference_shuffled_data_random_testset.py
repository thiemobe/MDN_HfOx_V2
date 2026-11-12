r"""
Interference/validation script for MDN models using CSV test data.

Supports both shuffled-data and iterative models:
- Shuffled models: --model-type shuffled (default) with --n-samples
- Iterative first: --model-type iterative_first
- Iterative second: --model-type iterative_second

All models use the same CSV test data and generate detailed predictions
with individual prediction results from all 5 shuffle runs.

Usage (Shuffled):
    python MDN_interference_shuffled_data_random_testset.py --model-type shuffled --n-samples 50
    python MDN_interference_shuffled_data_random_testset.py --model-type shuffled --n-samples 500



    1. For predictions obtained from a certain model
    & 'C:\Users\tbe\AppData\Local\Programs\Python\Python313\python.exe' MDN_interference_shuffled_data_random_testset.py --model-type shuffled --n-samples 50

    2. Powershell loop to run all sample sizes
    $sample_sizes = @(8, 12, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 316, 400, 500)
foreach ($n in $sample_sizes) {
    & 'C:\Users\tbe\AppData\Local\Programs\Python\Python313\python.exe' MDN_interference_shuffled_data_random_testset.py --model-type shuffled --n-samples $n --separate-states
}
    NOT NEEDED:
Usage (Iterative):
    python MDN_interference_shuffled_data_random_testset.py --model-type iterative_first
    python MDN_interference_shuffled_data_random_testset.py --model-type iterative_second --state 1.0
    & 'C:\Users\tbe\AppData\Local\Programs\Python\Python313\python.exe' MDN_interference_shuffled_data_random_testset.py --model-type iterative_first

    NOT NEEDED:
    when running just for Plot 4.: & 'C:\Users\tbe\AppData\Local\Programs\Python\Python313\python.exe' -c "from MDN_interference_shuffled_data_random_testset import validate_examples; validate_examples()"
    or with added GT-pdf based: & 'C:\Users\tbe\AppData\Local\Programs\Python\Python313\python.exe' -c "from MDN_interference_shuffled_data_random_testset import validate_examples; validate_examples(pdf_gt=True, gt_csv_path='voltage_sweep_results_10_cycles_cleaned.csv', gt_pdf_bin_width_uS=2.0, gt_pdf_max_width_V=0.06)"
    or with added GT-as vertical line: & 'C:\Users\tbe\AppData\Local\Programs\Python\Python313\python.exe' -c "from MDN_interference_shuffled_data_random_testset import validate_examples; validate_examples(include_gt=True, gt_csv_path='voltage_sweep_results_10_cycles_cleaned.csv', gt_line_half_length_uS=1.5)"
    
    & 'C:\Users\tbe\AppData\Local\Programs\Python\Python313\python.exe' -c "from MDN_interference_shuffled_data_random_testset import validate_examples, plot_set_pdf_for_four_voltages; plot_set_pdf_for_four_voltages()"
    
    """

import numpy as np
import torch
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd
import argparse
import json
import os
import sys

from sklearn.preprocessing import StandardScaler
from scipy.stats import norm
import joblib

from MDN import MDN
from MDN_predict import predict_distribution


def compute_mixture_quantiles(pi, mu, sigma, quantiles=(0.025, 0.05, 0.50, 0.95, 0.975, 0.99), n_grid=4096):
    """
    Compute quantiles for a 1D Gaussian mixture using CDF interpolation.

    Parameters
    ----------
    pi, mu, sigma : array-like
        Mixture weights, means, and standard deviations in the same units.
    quantiles : tuple of float
        Requested quantiles in [0, 1].
    n_grid : int
        Number of grid points used for CDF interpolation.

    Returns
    -------
    dict
        Mapping quantile value -> estimated quantile location.
    """
    pi_arr = np.asarray(pi, dtype=float)
    mu_arr = np.asarray(mu, dtype=float)
    sigma_arr = np.asarray(sigma, dtype=float)

    if not (np.all(np.isfinite(pi_arr)) and np.all(np.isfinite(mu_arr)) and np.all(np.isfinite(sigma_arr))):
        return {q: np.nan for q in quantiles}

    sigma_arr = np.maximum(sigma_arr, 1e-12)

    # Wide support to capture both modes and tails robustly.
    y_min = float(np.min(mu_arr - 8.0 * sigma_arr))
    y_max = float(np.max(mu_arr + 8.0 * sigma_arr))
    if not np.isfinite(y_min) or not np.isfinite(y_max) or y_min >= y_max:
        return {q: np.nan for q in quantiles}

    y_grid = np.linspace(y_min, y_max, int(n_grid))
    cdf = np.zeros_like(y_grid, dtype=float)
    for k in range(len(pi_arr)):
        cdf += pi_arr[k] * norm.cdf(y_grid, loc=mu_arr[k], scale=sigma_arr[k])

    # Numerical safety for interpolation on a monotone CDF.
    cdf = np.clip(cdf, 0.0, 1.0)
    cdf = np.maximum.accumulate(cdf)

    out = {}
    for q in quantiles:
        q_clipped = float(np.clip(q, 0.0, 1.0))
        out[q] = float(np.interp(q_clipped, cdf, y_grid, left=y_grid[0], right=y_grid[-1]))
    return out


def load_ground_truth_sweep_map(gt_csv_path):
    """
    Load ground-truth sweep values keyed by (PulseRole, V_applied).

    Ground truth per row is the mean conductance of columns 14, 19, 24
    (1-based indexing), i.e. G_after_1s, G_after_5s, G_after_10s.

    Only rows with PulseRole in {'sweep_set', 'sweep_reset'} are kept.

    Returns
    -------
    dict
        Mapping (pulse_role, voltage_rounded_3dp) -> np.ndarray of gt values [uS]
    """
    if not os.path.exists(gt_csv_path):
        raise FileNotFoundError(f"Ground truth CSV not found: {gt_csv_path}")

    df = pd.read_csv(gt_csv_path)

    # Prefer named columns; fall back to requested column positions if needed.
    if 'PulseRole' in df.columns:
        pulse_role = df['PulseRole'].astype(str)
    else:
        pulse_role = df.iloc[:, 3].astype(str)  # 1-based col 4

    if 'V_applied' in df.columns:
        v_applied = df['V_applied'].astype(float)
    else:
        v_applied = df.iloc[:, 4].astype(float)  # 1-based col 5

    if {'G_after_1s', 'G_after_5s', 'G_after_10s'}.issubset(df.columns):
        g1 = df['G_after_1s'].astype(float)
        g5 = df['G_after_5s'].astype(float)
        g10 = df['G_after_10s'].astype(float)
    else:
        # 1-based columns (14, 19, 24) -> 0-based (13, 18, 23)
        g1 = df.iloc[:, 13].astype(float)
        g5 = df.iloc[:, 18].astype(float)
        g10 = df.iloc[:, 23].astype(float)

    gt_mean_uS = ((g1 + g5 + g10) / 3.0).to_numpy() * 1e6
    pulse_role_arr = pulse_role.to_numpy()
    voltage_arr = v_applied.to_numpy()

    gt_map = {}
    for i in range(len(df)):
        role = str(pulse_role_arr[i]).strip()
        if role not in ('sweep_set', 'sweep_reset'):
            continue
        v = float(voltage_arr[i])
        gt = float(gt_mean_uS[i])
        if not np.isfinite(v) or not np.isfinite(gt):
            continue

        key = (role, round(v, 3))
        if key not in gt_map:
            gt_map[key] = []
        gt_map[key].append(gt)

    return {k: np.array(v, dtype=float) for k, v in gt_map.items()}


def load_shuffle_models(n_samples, base_dir='runs/all_sample_sizes_logarithmic_and_validated'):
    """
    Load all 5 models trained with different shuffles for given sample size.
    
    Parameters
    ----------
    n_samples : int
        Number of samples used in training (50, 100, ..., 500)
    base_dir : str
        Base directory containing all sample size runs
    
    Returns
    -------
    dict
        Mapping from run_name -> loaded model (in eval mode)
    """
    models_dir = os.path.join(base_dir, f'n{n_samples}')
    
    if not os.path.isdir(models_dir):
        raise FileNotFoundError(f"Models directory not found: {models_dir}")
    
    shuffle_models = {}
    
    print(f"\nLoading 5 shuffle-trained models from: {models_dir}")
    print("-" * 70)
    
    # Find all model files matching pattern: model_run<i>_shuffle_seed<seed>_<n_samples>samples_logarithmica.pt
    for run_idx in range(1, 6):
        shuffle_seed = n_samples * 1000 + (run_idx - 1)
        model_filename = f'model_run{run_idx}_shuffle_seed{shuffle_seed}_{n_samples}samples_logarithmic_with_outliers.pt'
        model_path = os.path.join(models_dir, model_filename)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Load checkpoint
        ckpt = torch.load(model_path, map_location='cpu')
        config = ckpt.get('config', {})
        state_dict = ckpt.get('state_dict', ckpt)
        
        # Create model with saved config
        model = MDN(
            input_dim=config.get('input_dim', 3),
            hidden_dim=config.get('hidden_dim', 64),
            n_components=config.get('n_components', 2),
            num_hidden_layers=config.get('hidden_layers', 1),
            dropout_rate=config.get('dropout', 0.3)
        )
        
        # Load state
        model.load_state_dict(state_dict)
        model.eval()
        
        run_name = f'shuffle_run{run_idx}_seed{shuffle_seed}'
        shuffle_models[run_name] = model
        print(f"✓ Loaded run {run_idx}/5: {run_name}")
    
    print("-" * 70)
    print(f"✓ All 5 shuffle-trained models loaded\n")
    
    return shuffle_models


def load_iterative_models(iteration='first', base_dir='runs'):
    """
    Load all 5 models trained with different shuffles for iterative dataset.
    
    Parameters
    ----------
    iteration : str
        'first' or 'second'
    base_dir : str
        Base directory containing trained models
    
    Returns
    -------
    tuple
        (models_dict, models_dir, scaler_X, scaler_y)
    """
    output_suffix = 'first_iterative' if iteration == 'first' else 'second_iterative'
    models_dir = os.path.join(base_dir, f'multi_shuffle_all_{output_suffix}')
    
    if not os.path.isdir(models_dir):
        raise FileNotFoundError(f"Models directory not found: {models_dir}")
    
    shuffle_models = {}
    
    print(f"\nLoading 5 shuffle-trained iterative models from: {models_dir}")
    print("-" * 70)
    
    # Find all model files
    model_files = [f for f in os.listdir(models_dir) if f.startswith('model_run') and f.endswith('.pt')]
    
    if len(model_files) != 5:
        print(f"WARNING: Expected 5 model files, found {len(model_files)}")
    
    model_files.sort()
    
    for run_idx, model_filename in enumerate(model_files, 1):
        model_path = os.path.join(models_dir, model_filename)
        
        # Load checkpoint
        ckpt = torch.load(model_path, map_location='cpu')
        config_dict = ckpt.get('config', {})
        state_dict = ckpt.get('state_dict', ckpt)
        
        # Create model with saved config
        model = MDN(
            input_dim=config_dict.get('input_dim', 3),
            hidden_dim=config_dict.get('hidden_dim', 64),
            n_components=config_dict.get('n_components', 2),
            num_hidden_layers=config_dict.get('hidden_layers', 1),
            dropout_rate=config_dict.get('dropout', 0.3)
        )
        
        # Load state
        model.load_state_dict(state_dict)
        model.eval()
        
        run_name = f'shuffle_run{run_idx}'
        shuffle_models[run_name] = model
        print(f"✓ Loaded run {run_idx}/5: {run_name} from {model_filename}")
    
    # Load scalers
    scaler_X = None
    scaler_y = None
    try:
        scaler_X = joblib.load(os.path.join(models_dir, f'scaler_X_with_outliers_{output_suffix}.joblib'))
        scaler_y = joblib.load(os.path.join(models_dir, f'scaler_y_with_outliers_{output_suffix}.joblib'))
        print(f'✓ Loaded scalers for {iteration} iterative')
    except Exception as e:
        print(f'ERROR: Could not load scalers: {e}')
        return shuffle_models, models_dir, None, None
    
    print("-" * 70)
    print(f"✓ All shuffle-trained iterative models loaded\n")
    
    return shuffle_models, models_dir, scaler_X, scaler_y


def load_data_from_csv(csv_path, max_samples=None, state_filter=None):
    """
    Load test data from CSV file with specific column mapping.
    
    Parameters
    ----------
    csv_path : str
        Path to CSV file
    max_samples : int, optional
        Maximum number of rows to load
    state_filter : {0, 1, None}, optional
        Filter by state: 0 for reset, 1 for set, None for all
    
    Returns
    -------
    tuple
        (X, y, metadata) where:
        - X: array of shape (n_samples, 3) with [state, g_before, voltage]
        - y: array of shape (n_samples,) with conductance output (G_after mean of 1s/5s/10s)
        - metadata: list of dicts with row info
    """
    
    print(f"\nLoading test data from CSV: {csv_path}")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Load CSV
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows from CSV")
    
    # Extract columns with proper mapping:
    # - Column 0 (State): 'reset' or 'set' -> 0.0 or 1.0
    # - Column 3 (V_applied): voltage in volts
    # - Column 9 (G_before): conductance before in µS
    # - Columns 11, 14, 17 (G_after_1s, G_after_5s, G_after_10s): mean of these is output
    
    state_str = df.iloc[:, 0].values  # 'reset' or 'set'
    state_vals = np.array([1.0 if s.lower() == 'set' else 0.0 for s in state_str])
    
    voltage = df.iloc[:, 3].values.astype(float)  # V_applied
    g_before = df.iloc[:, 9].values.astype(float) * 1e6  # G_before in µS (convert from S)
    
    # Output: mean of G_after across 1s, 5s, 10s measurements (columns 11, 14, 17)
    g_after_1s = df.iloc[:, 11].values.astype(float) * 1e6  # Convert to µS
    g_after_5s = df.iloc[:, 14].values.astype(float) * 1e6  # Convert to µS
    g_after_10s = df.iloc[:, 17].values.astype(float) * 1e6  # Convert to µS
    g_after_mean = (g_after_1s + g_after_5s + g_after_10s) / 3.0
    
    # Build feature matrix [state, g_before, voltage]
    X_list = []
    y_list = []
    meta_list = []
    
    for i in range(len(df)):
        # Validate all values are finite and positive
        if not (np.isfinite(g_before[i]) and g_before[i] > 0 and 
                np.isfinite(voltage[i]) and voltage[i] > 0 and
                np.isfinite(g_after_mean[i]) and g_after_mean[i] > 0):
            continue
        
        # Apply state filter if specified
        if state_filter is not None and state_vals[i] != state_filter:
            continue
        
        X_list.append([state_vals[i], g_before[i], voltage[i]])
        y_list.append(g_after_mean[i])
        meta_list.append({
            'row_idx': i,
            'state': 'set' if state_vals[i] == 1.0 else 'reset',
            'voltage': float(voltage[i]),
            'g_before': float(g_before[i]),
            'g_after_1s': float(g_after_1s[i]),
            'g_after_5s': float(g_after_5s[i]),
            'g_after_10s': float(g_after_10s[i]),
        })
        
        if max_samples is not None and len(X_list) >= max_samples:
            break
    
    if len(X_list) == 0:
        raise RuntimeError("No valid samples loaded from CSV")
    
    X = np.array(X_list, dtype=float)
    y = np.array(y_list, dtype=float)
    
    print(f"Loaded {len(X)} valid samples")
    if state_filter is not None:
        state_name = 'set' if state_filter == 1.0 else 'reset'
        print(f"Filtered to {state_name} state: {len(X)} samples")
    
    return X, y, meta_list
#    & 'C:\Users\tbe\AppData\Local\Programs\Python\Python313\python.exe' MDN_interference_shuffled_data_random_testset.py --model-type shuffled --n-samples 50

# & 'C:\Users\tbe\AppData\Local\Programs\Python\Python313\python.exe' -c "from MDN_interference_shuffled_data_random_testset import validate_examples; validate_examples()"
def validate_examples(
    include_gt=False,
    pdf_gt=False,
    gt_csv_path='voltage_sweep_results_10_cycles.csv',
    gt_line_half_length_uS=1.0,
    gt_pdf_bin_width_uS=2.0,
    gt_pdf_max_width_V=0.06,
    **kwargs,
):
    """
    Validate model on comprehensive validation examples.
    
    Examples:
    - RESET cases (state=0) with G_before=120µS at all voltages 0.1V to 1.5V (0.1V steps)
    - SET cases (state=1) with G_before=2µS at all voltages 0.1V to 1.5V (0.1V steps)
    
    Total: 30 examples (15 voltages × 2 states)
    
    Uses model_run1_shuffle_seed125000_125samples_logarithmic.pt (125-sample model)

    Parameters
    ----------
    include_gt : bool
        If True, overlay ground-truth values as short vertical line markers.
    pdf_gt : bool
        If True, overlay ground-truth as PDF-style vertical bins per voltage.
    gt_csv_path : str
        CSV containing PulseRole, V_applied and G_after columns.
    gt_line_half_length_uS : float
        Half-length of each GT vertical line marker in uS.
    gt_pdf_bin_width_uS : float
        Conductance bin width in uS for PDF-style GT bars.
    gt_pdf_max_width_V : float
        Maximum horizontal width (in voltage axis units) for PDF GT bars.
    """
    
    # Optional alias support for CLI-style hyphenated names, e.g. {'pdf-gt': True}.
    include_gt = kwargs.get('include-gt', include_gt)
    pdf_gt = kwargs.get('pdf-gt', pdf_gt)
    gt_csv_path = kwargs.get('gt-csv-path', gt_csv_path)
    gt_line_half_length_uS = kwargs.get('gt-line-half-length-uS', gt_line_half_length_uS)
    gt_pdf_bin_width_uS = kwargs.get('gt-pdf-bin-width-uS', gt_pdf_bin_width_uS)
    gt_pdf_max_width_V = kwargs.get('gt-pdf-max-width-V', gt_pdf_max_width_V)

    # Generate examples for all voltages from 0.1V to 1.5V in 0.1V steps
    voltages = np.round(np.arange(0.1, 1.55, 0.1), 2)  # [0.1, 0.2, ..., 1.5]
    examples = []
    
    # RESET cases (state=0, G_before=120µS)
    for v in voltages:
        examples.append({
            'state': 0,
            'voltage': v,
            'g_before_S': 0.00010824,#mean of measurements
            'label': f'RESET, V={v:.1f}V, G_before=120µS'
        })
    
    # SET cases (state=1, G_before=2µS)
    for v in voltages:
        examples.append({
            'state': 1,
            'voltage': v,
            'g_before_S': 0.00000898, #mean of measurements
            'label': f'SET, V={v:.1f}V, G_before=4µS'
        })
    
    print("\n" + "=" * 80)
    print("VALIDATING COMPREHENSIVE EXAMPLES")
    print("=" * 80)
    
    # Load single model: model_run4_shuffle_seed125003_500samples_logarithmic.pt
    model_dir = os.path.join('runs/all_sample_sizes_logarithmic_and_validated', 'n125')
    model_path = os.path.join(model_dir, 'model_run5_shuffle_seed125004_125samples_logarithmic.pt')
    
    print(f"\nLoading model from: {model_path}")
    
    if not os.path.exists(model_path):
        print(f"ERROR: Model file not found: {model_path}")
        return
    
    # Load checkpoint
    ckpt = torch.load(model_path, map_location='cpu')
    config = ckpt.get('config', {})
    state_dict = ckpt.get('state_dict', ckpt)
    
    # Create model
    model = MDN(
        input_dim=config.get('input_dim', 3),
        hidden_dim=config.get('hidden_dim', 64),
        n_components=config.get('n_components', 2),
        num_hidden_layers=config.get('hidden_layers', 1),
        dropout_rate=config.get('dropout', 0.3)
    )
    model.load_state_dict(state_dict)
    model.eval()
    print("✓ Model loaded successfully")
    
    # Load scalers
    try:
        scaler_X = joblib.load(os.path.join(model_dir, 'scaler_X_125samples_logarithmic.joblib'))
        scaler_y = joblib.load(os.path.join(model_dir, 'scaler_y_125samples_logarithmic.joblib'))
        print("✓ Scalers loaded successfully")
    except Exception as e:
        print(f"ERROR: Could not load scalers: {e}")
        return
    
    # Prediction range
    y_range_plot = np.linspace(-50.0, 200.0, 400)
    
    # Process examples
    print("\n" + "=" * 80)
    print(f"PREDICTIONS FOR {len(examples)} EXAMPLES")
    print("=" * 80)
    
    results = []
    
    for idx, example in enumerate(examples, 1):
        print(f"\n[{idx}/{len(examples)}] {example['label']}")
        print("-" * 80)
        
        state_val = float(example['state'])
        voltage_val = float(example['voltage'])
        g_before_uS = float(example['g_before_S']) * 1e6  # Convert S to µS
        
        # Build feature vector [state, g_before, voltage]
        x_raw = np.array([state_val, g_before_uS, voltage_val], dtype=float)
        
        # Scale input
        x_cont = np.array([g_before_uS, voltage_val]).reshape(1, -1)
        x_cont_scaled = scaler_X.transform(x_cont)[0]
        x_scaled = np.concatenate([[state_val], x_cont_scaled]).astype(float)
        
        # Get prediction from model
        _, (pi, mu, sigma) = predict_distribution(model, x_scaled, y_range_plot)
        
        # Unscale outputs
        mu_unscaled = mu * scaler_y.scale_[0] + scaler_y.mean_[0]
        sigma_unscaled = sigma * scaler_y.scale_[0]
        
        # Compute mixture statistics
        pi_arr = np.array(pi)
        mu_arr = np.array(mu_unscaled)
        sigma_arr = np.array(sigma_unscaled)
        
        mixture_mean = np.sum(pi_arr * mu_arr)
        mixture_var = np.sum(pi_arr * (sigma_arr**2 + mu_arr**2)) - mixture_mean**2
        mixture_var = np.maximum(mixture_var, 0)
        mixture_std = np.sqrt(mixture_var)
        
        # Display results
        state_name = "SET" if state_val == 1.0 else "RESET"
        print(f"State: {state_name}")
        print(f"Voltage: {voltage_val:.2f}V")
        print(f"G_before: {g_before_uS:.2f}µS")
        
        print(f"\nMixture Components:")
        for k in range(len(pi)):
            print(f"  Component {k+1}: π={pi[k]:.4f}, μ={mu_unscaled[k]:.2f}µS, σ={sigma_unscaled[k]:.2f}µS")
        
        print(f"\nMixture Statistics:")
        print(f"  Mean: {mixture_mean:.2f}µS")
        print(f"  Std:  {mixture_std:.2f}µS")
        print(f"  Range: [{mixture_mean - mixture_std:.2f}, {mixture_mean + mixture_std:.2f}]µS")
        
        results.append({
            'example_idx': idx,
            'state': state_name,
            'voltage': voltage_val,
            'g_before_uS': g_before_uS,
            'mixture_mean_uS': mixture_mean,
            'mixture_std_uS': mixture_std,
            'pi_1': pi[0],
            'mu_1_uS': mu_unscaled[0],
            'sigma_1_uS': sigma_unscaled[0],
            'pi_2': pi[1] if len(pi) > 1 else np.nan,
            'mu_2_uS': mu_unscaled[1] if len(mu_unscaled) > 1 else np.nan,
            'sigma_2_uS': sigma_unscaled[1] if len(sigma_unscaled) > 1 else np.nan,
        })
    
    # Print summary table
    print("\n" + "=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80 + "\n")
    
    df_results = pd.DataFrame(results)
    print(df_results.to_string(index=False))
    
    # Save results to CSV
    output_file = "validation_examples_model_5_125samples.csv"
    df_results.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"\n✓ Results saved to: {output_file}")

    # Optional ground-truth mapping for overlays
    gt_map = None
    if include_gt or pdf_gt:
        try:
            gt_map = load_ground_truth_sweep_map(gt_csv_path)
            print(f"✓ Loaded GT sweep map from: {gt_csv_path}")
        except Exception as e:
            print(f"WARNING: Could not load GT CSV ({gt_csv_path}): {e}")
            gt_map = None

    # Plot predictions and optional GT overlays
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    state_specs = [
        ('RESET', 'sweep_reset', axes[0], 'tab:red'),
        ('SET', 'sweep_set', axes[1], 'tab:blue'),
    ]

    for state_label, pulse_role, ax, color in state_specs:
        dfi = df_results[df_results['state'] == state_label].sort_values('voltage')
        if len(dfi) == 0:
            ax.set_title(f'{state_label} (no samples)')
            continue

        x_vals = dfi['voltage'].to_numpy(dtype=float)
        y_mean = dfi['mixture_mean_uS'].to_numpy(dtype=float)
        y_std = dfi['mixture_std_uS'].to_numpy(dtype=float)

        ax.plot(x_vals, y_mean, '-o', color=color, linewidth=2, markersize=4, label='MDN mean')
        ax.fill_between(x_vals, y_mean - y_std, y_mean + y_std, color=color, alpha=0.18, label='MDN ±1σ')

        # Overlay GT as short vertical markers
        if include_gt and gt_map is not None:
            gt_count = 0
            for v in np.unique(x_vals):
                gt_vals = gt_map.get((pulse_role, round(float(v), 3)), np.array([], dtype=float))
                if gt_vals.size == 0:
                    continue
                gt_count += gt_vals.size
                ax.vlines(
                    np.full(gt_vals.shape, v),
                    gt_vals - gt_line_half_length_uS,
                    gt_vals + gt_line_half_length_uS,
                    color='black',
                    alpha=0.45,
                    linewidth=1.0,
                    label='GT lines' if v == np.unique(x_vals)[0] else None,
                )
            print(f"{state_label}: plotted {gt_count} GT line markers")

        # Overlay GT as PDF-style vertical bins (segment height=bin width, segment width=PDF)
        if pdf_gt and gt_map is not None:
            pdf_segments = 0
            unique_x = np.unique(x_vals)
            for v in unique_x:
                gt_vals = gt_map.get((pulse_role, round(float(v), 3)), np.array([], dtype=float))
                if gt_vals.size == 0:
                    continue

                if gt_vals.size == 1:
                    # Single point fallback: draw a single bin-segment with full width.
                    y0 = gt_vals[0] - 0.5 * gt_pdf_bin_width_uS
                    y1 = gt_vals[0] + 0.5 * gt_pdf_bin_width_uS
                    x0 = v - gt_pdf_max_width_V if pulse_role == 'sweep_reset' else v
                    rect = Rectangle((x0, y0), gt_pdf_max_width_V, y1 - y0,
                                     facecolor='gray', alpha=0.30, edgecolor='none')
                    ax.add_patch(rect)
                    pdf_segments += 1
                    continue

                y_min = np.min(gt_vals)
                y_max = np.max(gt_vals)
                bins = np.arange(y_min, y_max + gt_pdf_bin_width_uS, gt_pdf_bin_width_uS)
                if bins.size < 2:
                    bins = np.array([y_min - 0.5 * gt_pdf_bin_width_uS, y_max + 0.5 * gt_pdf_bin_width_uS])

                hist, edges = np.histogram(gt_vals, bins=bins, density=True)
                hmax = np.max(hist) if hist.size > 0 else 0.0
                if hmax <= 0:
                    continue

                for h, y0, y1 in zip(hist, edges[:-1], edges[1:]):
                    if h <= 0:
                        continue
                    width_v = (h / hmax) * gt_pdf_max_width_V
                    x0 = v - width_v if pulse_role == 'sweep_reset' else v
                    rect = Rectangle((x0, y0), width_v, y1 - y0,
                                     facecolor='gray', alpha=0.25, edgecolor='none')
                    ax.add_patch(rect)
                    pdf_segments += 1

            print(f"{state_label}: plotted {pdf_segments} GT PDF segments")

        ax.set_title(f'{state_label} sweep ({pulse_role})')
        ax.set_xlabel('Voltage [V]')
        ax.grid(alpha=0.25)

    axes[0].set_ylabel('Conductance [uS]')
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        axes[0].legend(loc='best')
    handles, labels = axes[1].get_legend_handles_labels()
    if handles:
        axes[1].legend(loc='best')

    plt.suptitle('validate_examples: MDN predictions with optional GT overlays')
    plt.tight_layout()
    plt.show()
    
    return df_results


def plot_set_pdf_for_four_voltages(
    voltages=(0.6, 0.7, 0.8, 0.9),
    g_before_uS=55.0,
    state='set',
    model_dir=os.path.join('runs/all_sample_sizes_logarithmic_and_validated', 'n500'),
    model_filename='model_run3_shuffle_seed500002_500samples_logarithmic.pt',
    scaler_x_filename='scaler_X_500samples_logarithmic.joblib',
    scaler_y_filename='scaler_y_500samples_logarithmic.joblib',
    conductance_range_uS=None,
):
    """
    Plot the predicted output PDF for a SET input at four fixed voltages.

    The function uses the saved PT checkpoint as the predictor and plots one
    PDF curve per voltage on the same conductance axis.
    """

    state_value = 1.0 if str(state).strip().lower() == 'set' else 0.0
    state_name = 'SET' if state_value == 1.0 else 'RESET'

    if conductance_range_uS is None:
        conductance_range_uS = np.linspace(-50.0, 200.0, 500)

    model_path = os.path.join(model_dir, model_filename)

    print("\n" + "=" * 80)
    print("PLOTTING SET-STATE PDF FOR FOUR VOLTAGES")
    print("=" * 80)
    print(f"State: {state_name}")
    print(f"Model: {model_path}")

    if not os.path.exists(model_path):
        print(f"ERROR: Model file not found: {model_path}")
        return None

    ckpt = torch.load(model_path, map_location='cpu')
    config = ckpt.get('config', {})
    state_dict = ckpt.get('state_dict', ckpt)

    model = MDN(
        input_dim=config.get('input_dim', 3),
        hidden_dim=config.get('hidden_dim', 64),
        n_components=config.get('n_components', 2),
        num_hidden_layers=config.get('hidden_layers', 1),
        dropout_rate=config.get('dropout', 0.3)
    )
    model.load_state_dict(state_dict)
    model.eval()
    print("✓ Model loaded successfully")

    try:
        scaler_X = joblib.load(os.path.join(model_dir, scaler_x_filename))
        scaler_y = joblib.load(os.path.join(model_dir, scaler_y_filename))
        print("✓ Scalers loaded successfully")
    except Exception as e:
        print(f"ERROR: Could not load scalers: {e}")
        return None

    fig, ax = plt.subplots(figsize=(6, 6))
    colors = plt.cm.Blues(np.linspace(0.3, 0.9, len(voltages)))
    curve_data = []

    for voltage, color in zip(voltages, colors):
        x_cont = np.array([g_before_uS, float(voltage)], dtype=float).reshape(1, -1)
        x_cont_scaled = scaler_X.transform(x_cont)[0]
        x_scaled = np.concatenate([[state_value], x_cont_scaled]).astype(float)

        _, (pi, mu, sigma) = predict_distribution(model, x_scaled, conductance_range_uS)

        mu_unscaled = mu * scaler_y.scale_[0] + scaler_y.mean_[0]
        sigma_unscaled = sigma * scaler_y.scale_[0]

        pdf = np.zeros_like(conductance_range_uS, dtype=float)
        for component_idx in range(len(pi)):
            pdf += pi[component_idx] * norm.pdf(
                conductance_range_uS,
                mu_unscaled[component_idx],
                sigma_unscaled[component_idx],
            )

        curve_data.append({
            'voltage': float(voltage),
            'pdf': pdf,
            'mixture_mean_uS': float(np.sum(np.array(pi) * np.array(mu_unscaled))),
        })
        ax.plot(
            conductance_range_uS,
            pdf,
            linewidth=2.0,
            color=color,
            label=f'{voltage:.1f} V',
        )

    ax.set_title(f'Predicted output PDF for {state_name} state, G_before = {g_before_uS:.0f} µS')
    ax.set_xlabel('Conductance [µS]')
    ax.set_ylabel('Probability density')
    ax.set_xlim(-50.0, 200.0)
    ax.set_xticks([0, 50, 100, 150, 200])
    ax.grid(alpha=0.25)
    ax.legend(title='Voltage')
    plt.tight_layout()
    plt.show()

    for item in curve_data:
        print(
            f"V={item['voltage']:.1f} V: mixture mean={item['mixture_mean_uS']:.2f} µS, "
            f"peak pdf={np.max(item['pdf']):.4f}"
        )

    return {
        'conductance_range_uS': conductance_range_uS,
        'curves': curve_data,
        'figure': fig,
        'axes': ax,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate MDN models on CSV test data (shuffled or iterative)"
    )
    parser.add_argument(
        "--model-type",
        type=str,
        choices=['shuffled', 'iterative_first', 'iterative_second'],
        default='shuffled',
        help="Model type: shuffled (default), iterative_first, or iterative_second"
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=None,
        help="Sample size used during training (required for shuffled models)"
    )
    parser.add_argument(
        "--csv-file",
        default="csv_files/test_samples_from_backup_remaining.csv",
        help="Path to CSV test data file"
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output CSV file (default: auto-generated based on model type)"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Maximum number of samples to process"
    )
    parser.add_argument(
        "--state",
        type=float,
        default=None,
        help="Filter by state: 1.0 for Set, 0.0 for Reset, None for both (default: None)"
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default="runs",
        help="Base directory containing trained models (default: runs)"
    )
    parser.add_argument(
        "--separate-states",
        action='store_true',
        help="Separate predictions into _set and _reset files (shuffled models only)"
    )
    
    args = parser.parse_args()
    
    # Determine model type and validate arguments
    if args.model_type == 'shuffled':
        if args.n_samples is None:
            print("ERROR: --n-samples is required for shuffled models")
            return
        models_dir = os.path.join(args.models_dir, 'all_sample_sizes_logarithmic_and_validated')
        iteration = None
        output_suffix = f'shuffled_n{args.n_samples}'
    else:
        iteration = args.model_type.replace('iterative_', '')
        args.n_samples = None
        models_dir = args.models_dir
        output_suffix = f'iterative_{iteration}'
    
    # Set default output file
    if args.out is None:
        state_str = f'_{int(args.state)}' if args.state is not None else ''
        args.out = f"csv_files/mdn_predictions_final_models_random_dataset_predictions_with_outliers_{output_suffix}{state_str}.csv"
    
    # Load models
    print("\n" + "=" * 70)
    print("LOADING MODELS FOR INFERENCE")
    print("=" * 70)
    
    if args.model_type == 'shuffled':
        try:
            shuffle_models = load_shuffle_models(args.n_samples, models_dir)
            scaler_X = None
            scaler_y = None
            try:
                scaler_X = joblib.load(os.path.join(models_dir, f'n{args.n_samples}', f'scaler_X_{args.n_samples}samples_logarithmic_with_outliers.joblib'))
                scaler_y = joblib.load(os.path.join(models_dir, f'n{args.n_samples}', f'scaler_y_{args.n_samples}samples_logarithmic_with_outliers.joblib'))
                print(f'✓ Loaded scalers from {models_dir}/n{args.n_samples}')
            except Exception as e:
                print(f'ERROR: Could not load scalers: {e}')
                return
        except Exception as e:
            print(f"ERROR loading models: {e}")
            return
    else:
        try:
            shuffle_models, models_loaded_dir, scaler_X, scaler_y = load_iterative_models(iteration, models_dir)
            if scaler_X is None or scaler_y is None:
                print(f"ERROR: Could not load scalers for {iteration} iterative models")
                return
        except Exception as e:
            print(f"ERROR loading iterative models: {e}")
            return
    
    # Load test data from CSV
    print("\n" + "=" * 70)
    print("LOADING TEST DATA FROM CSV")
    print("=" * 70)
    
    try:
        X_all, y_true_all, meta_list_all = load_data_from_csv(
            args.csv_file,
            max_samples=args.max_samples,
            state_filter=None  # Load all, will filter per state if needed
        )
    except Exception as e:
        print(f"ERROR loading CSV data: {e}")
        return
    
    if X_all.shape[0] == 0:
        print("No valid samples after preprocessing.")
        return
    
    # Determine which states to process
    states_to_process = []
    if args.state is not None:
        states_to_process = [args.state]
    else:
        # For iterative models without explicit state, process both states separately
        if args.model_type != 'shuffled':
            states_to_process = [1.0, 0.0]
        elif args.separate_states:
            # For shuffled models with --separate-states flag
            states_to_process = [1.0, 0.0]
        else:
            states_to_process = [None]  # Process all for shuffled
    
    # Process each state
    for state_filter in states_to_process:
        # Filter data by state if needed
        if state_filter is not None:
            state_mask = X_all[:, 0] == state_filter
            X = X_all[state_mask]
            y_true = y_true_all[state_mask]
            meta_list = [meta_list_all[i] for i in range(len(state_mask)) if state_mask[i]]
            state_name = 'set' if state_filter == 1.0 else 'reset'
            print(f"\nFiltered to {state_name} state: {X.shape[0]} samples")
        else:
            X = X_all
            y_true = y_true_all
            meta_list = meta_list_all
            state_name = None
        
        if X.shape[0] == 0:
            print(f"No valid samples for state {state_filter}.")
            continue
        
        # Determine output file for this state
        if state_filter is not None and args.state is None:
            # For iterative models processing both states, use state-specific filenames
            out_file = args.out.replace('.csv', f'_{state_name}.csv')
        else:
            out_file = args.out
        
        # Prediction range
        y_range_plot = np.linspace(-50.0, 200.0, 400)
        
        # Generate predictions
        print("\n" + "=" * 80)
        print("GENERATING PREDICTIONS FROM ALL 5 MODELS")
        if state_filter is not None:
            print(f"State: {state_name.upper()}")
        print("=" * 80)
        
        rows = []
        
        print(f"\n=== Conductance Values for First 30 Samples ===")
        for i in range(min(30, len(X))):
            state_display = 'SET' if int(X[i, 0]) == 1 else 'RESET'
            print(f"Sample {i}: State={state_display}, G_before={X[i, 1]:.2f} µS, Voltage={X[i, 2]:.3f} V, y_true={y_true[i]:.2f} µS")
        print("=" * 80 + "\n")
        
        for i, x in enumerate(X):
            if (i + 1) % 50 == 0 or i == 0:
                print(f"Processing sample {i + 1}/{len(X)}...")
            
            # Scale input
            if scaler_X is not None:
                x_cont = np.array(x[1:]).reshape(1, -1)
                x_cont_scaled = scaler_X.transform(x_cont)[0]
                x_scaled = np.concatenate([[x[0]], x_cont_scaled]).astype(float)
            else:
                x_scaled = x

            # Get predictions from EACH shuffle-trained model
            # Store individual components for each model
            shuffle_components = []  # List of dicts with pi, mu, sigma for each run
            
            for model_idx, (run_name, model) in enumerate(shuffle_models.items()):
                _, (pi, mu, sigma) = predict_distribution(model, x_scaled, y_range_plot)
                
                # Check for invalid model outputs
                if not (np.all(np.isfinite(pi)) and np.all(np.isfinite(mu)) and np.all(np.isfinite(sigma))):
                    # Model produced NaN or inf - use nan placeholder
                    shuffle_components.append({
                        'pi': [np.nan] * len(pi),
                        'mu': [np.nan] * len(mu),
                        'sigma': [np.nan] * len(sigma),
                        'valid': False
                    })
                    continue
                
                # Unscale outputs
                mu_unscaled = mu * scaler_y.scale_[0] + scaler_y.mean_[0]
                sigma_unscaled = sigma * scaler_y.scale_[0]
                
                # Check for invalid unscaled values
                if not (np.all(np.isfinite(mu_unscaled)) and np.all(np.isfinite(sigma_unscaled))):
                    shuffle_components.append({
                        'pi': [np.nan] * len(pi),
                        'mu': [np.nan] * len(mu_unscaled),
                        'sigma': [np.nan] * len(sigma_unscaled),
                        'valid': False
                    })
                    continue
                
                # Store individual component parameters
                shuffle_components.append({
                    'pi': pi.tolist() if hasattr(pi, 'tolist') else list(pi),
                    'mu': mu_unscaled.tolist() if hasattr(mu_unscaled, 'tolist') else list(mu_unscaled),
                    'sigma': sigma_unscaled.tolist() if hasattr(sigma_unscaled, 'tolist') else list(sigma_unscaled),
                    'valid': True
                })
            
            true_val_uS = y_true[i]
            meta = meta_list[i]
            
            # Build row with predictions from all 5 shuffle runs
            row = {
                "sample_idx": i,
                "row_idx": meta['row_idx'],
                "state": meta['state'],
                "voltage": meta['voltage'],
                "g_before": meta['g_before'],
                "g_after_1s": meta['g_after_1s'],
                "g_after_5s": meta['g_after_5s'],
                "g_after_10s": meta['g_after_10s'],
                "y_measured_uS": true_val_uS,
            }
            
            # Add individual component parameters and computed statistics for each shuffle run
            for run_idx, components in enumerate(shuffle_components, 1):
                if components['valid']:
                    # Save individual component parameters
                    n_components = len(components['pi'])
                    for comp_idx in range(n_components):
                        row[f"shuffle_run{run_idx}_pi_{comp_idx+1}"] = components['pi'][comp_idx]
                        row[f"shuffle_run{run_idx}_mu_{comp_idx+1}"] = components['mu'][comp_idx]
                        row[f"shuffle_run{run_idx}_sigma_{comp_idx+1}"] = components['sigma'][comp_idx]
                    
                    # Compute mixture mean and std for reference/diagnostics
                    pi_arr = np.array(components['pi'])
                    mu_arr = np.array(components['mu'])
                    sigma_arr = np.array(components['sigma'])
                    mixture_mean = np.sum(pi_arr * mu_arr)
                    with np.errstate(invalid='ignore'):
                        mixture_var = np.sum(pi_arr * (sigma_arr**2 + mu_arr**2)) - mixture_mean**2
                    mixture_var = np.maximum(mixture_var, 0)
                    mixture_std = np.sqrt(mixture_var)

                    # Variance decomposition: within-mode + between-mode.
                    within_var = np.sum(pi_arr * (sigma_arr ** 2))
                    between_var = np.sum(pi_arr * ((mu_arr - mixture_mean) ** 2))

                    # Mixture quantiles from the full GMM CDF.
                    mix_q = compute_mixture_quantiles(
                        pi_arr,
                        mu_arr,
                        sigma_arr,
                        quantiles=(0.025, 0.05, 0.50, 0.95, 0.975, 0.99),
                    )

                    # Component quantiles (per Gaussian).
                    for comp_idx in range(n_components):
                        comp_mu = components['mu'][comp_idx]
                        comp_sigma = max(float(components['sigma'][comp_idx]), 1e-12)
                        row[f"shuffle_run{run_idx}_comp{comp_idx+1}_q025_uS"] = float(norm.ppf(0.025, loc=comp_mu, scale=comp_sigma))
                        row[f"shuffle_run{run_idx}_comp{comp_idx+1}_q05_uS"] = float(norm.ppf(0.05, loc=comp_mu, scale=comp_sigma))
                        row[f"shuffle_run{run_idx}_comp{comp_idx+1}_q50_uS"] = float(norm.ppf(0.50, loc=comp_mu, scale=comp_sigma))
                        row[f"shuffle_run{run_idx}_comp{comp_idx+1}_q95_uS"] = float(norm.ppf(0.95, loc=comp_mu, scale=comp_sigma))
                        row[f"shuffle_run{run_idx}_comp{comp_idx+1}_q975_uS"] = float(norm.ppf(0.975, loc=comp_mu, scale=comp_sigma))
                        row[f"shuffle_run{run_idx}_comp{comp_idx+1}_q99_uS"] = float(norm.ppf(0.99, loc=comp_mu, scale=comp_sigma))
                    
                    row[f"shuffle_run{run_idx}_mixture_mean_uS"] = mixture_mean
                    row[f"shuffle_run{run_idx}_mixture_std_uS"] = mixture_std
                    row[f"shuffle_run{run_idx}_within_var_uS2"] = within_var
                    row[f"shuffle_run{run_idx}_between_var_uS2"] = between_var
                    row[f"shuffle_run{run_idx}_mixture_q025_uS"] = mix_q[0.025]
                    row[f"shuffle_run{run_idx}_mixture_q05_uS"] = mix_q[0.05]
                    row[f"shuffle_run{run_idx}_mixture_q50_uS"] = mix_q[0.50]
                    row[f"shuffle_run{run_idx}_mixture_q95_uS"] = mix_q[0.95]
                    row[f"shuffle_run{run_idx}_mixture_q975_uS"] = mix_q[0.975]
                    row[f"shuffle_run{run_idx}_mixture_q99_uS"] = mix_q[0.99]
                    row[f"shuffle_run{run_idx}_n_components"] = n_components
                    
                    # Residual (based on mixture mean)
                    if not np.isnan(true_val_uS):
                        row[f"shuffle_run{run_idx}_residual_uS"] = true_val_uS - mixture_mean
                    else:
                        row[f"shuffle_run{run_idx}_residual_uS"] = None
                else:
                    # Invalid predictions - mark all as NaN
                    n_components = len(shuffle_components[0]['pi'])  # Use first run's component count
                    for comp_idx in range(n_components):
                        row[f"shuffle_run{run_idx}_pi_{comp_idx+1}"] = np.nan
                        row[f"shuffle_run{run_idx}_mu_{comp_idx+1}"] = np.nan
                        row[f"shuffle_run{run_idx}_sigma_{comp_idx+1}"] = np.nan
                        row[f"shuffle_run{run_idx}_comp{comp_idx+1}_q025_uS"] = np.nan
                        row[f"shuffle_run{run_idx}_comp{comp_idx+1}_q05_uS"] = np.nan
                        row[f"shuffle_run{run_idx}_comp{comp_idx+1}_q50_uS"] = np.nan
                        row[f"shuffle_run{run_idx}_comp{comp_idx+1}_q95_uS"] = np.nan
                        row[f"shuffle_run{run_idx}_comp{comp_idx+1}_q975_uS"] = np.nan
                        row[f"shuffle_run{run_idx}_comp{comp_idx+1}_q99_uS"] = np.nan
                    row[f"shuffle_run{run_idx}_mixture_mean_uS"] = np.nan
                    row[f"shuffle_run{run_idx}_mixture_std_uS"] = np.nan
                    row[f"shuffle_run{run_idx}_within_var_uS2"] = np.nan
                    row[f"shuffle_run{run_idx}_between_var_uS2"] = np.nan
                    row[f"shuffle_run{run_idx}_mixture_q025_uS"] = np.nan
                    row[f"shuffle_run{run_idx}_mixture_q05_uS"] = np.nan
                    row[f"shuffle_run{run_idx}_mixture_q50_uS"] = np.nan
                    row[f"shuffle_run{run_idx}_mixture_q95_uS"] = np.nan
                    row[f"shuffle_run{run_idx}_mixture_q975_uS"] = np.nan
                    row[f"shuffle_run{run_idx}_mixture_q99_uS"] = np.nan
                    row[f"shuffle_run{run_idx}_n_components"] = np.nan
                    row[f"shuffle_run{run_idx}_residual_uS"] = np.nan
            
            rows.append(row)
        
        # Save output
        df_out = pd.DataFrame(rows)
        os.makedirs(os.path.dirname(out_file) or '.', exist_ok=True)
        df_out.to_csv(out_file, index=False, encoding="utf-8-sig")
        
        print(f"\n" + "=" * 80)
        print(f"✓ Wrote predictions to {out_file}")
        print(f"=" * 80)
        print(f"\nOutput CSV contains:")
        print(f"  - Sample metadata: row_idx, state, voltage, g_before")
        print(f"  - Ground truth: y_measured_uS (mean of G_after_1s, 5s, 10s)")
        print(f"  - Individual component parameters for each shuffle run:")
        print(f"    * shuffle_run{run_idx}_pi_1, shuffle_run{run_idx}_pi_2 (mixture weights)")
        print(f"    * shuffle_run{run_idx}_mu_1, shuffle_run{run_idx}_mu_2 (component means)")
        print(f"    * shuffle_run{run_idx}_sigma_1, shuffle_run{run_idx}_sigma_2 (component stds)")
        print(f"  - Derived statistics:")
        print(f"    * shuffle_run{run_idx}_mixture_mean_uS, shuffle_run{run_idx}_mixture_std_uS")
        print(f"    * shuffle_run{run_idx}_within_var_uS2, shuffle_run{run_idx}_between_var_uS2")
        print(f"    * shuffle_run{run_idx}_mixture_q025_uS, q05_uS, q50_uS, q95_uS, q975_uS, q99_uS")
        print(f"    * shuffle_run{run_idx}_comp1_q025_uS..q99_uS, shuffle_run{run_idx}_comp2_q025_uS..q99_uS")
        print(f"    * shuffle_run{run_idx}_n_components (number of components)")
        print(f"    * shuffle_run{run_idx}_residual_uS (ground truth - mixture mean)")
        
        # Count NaN values in output
        print(f"\n⚠ NaN Value Statistics (Component Parameters):")
        has_nans = False
        for run_idx in range(1, 6):
            for comp_idx in range(1, 3):  # 2 components
                for param in ['pi', 'mu', 'sigma']:
                    col = f'shuffle_run{run_idx}_{param}_{comp_idx}'
                    if col in df_out.columns:
                        n_nan = df_out[col].isna().sum()
                        if n_nan > 0:
                            print(f"  - {col}: {n_nan}/{len(df_out)} samples ({n_nan/len(df_out)*100:.1f}%)")
                            has_nans = True
        if not has_nans:
            print(f"  ✓ No NaN values in component parameters")
        
        print(f"\n⚠ NaN Value Statistics (Derived Statistics):")
        has_nans = False
        for run_idx in range(1, 6):
            for col in [f'shuffle_run{run_idx}_mixture_mean_uS', f'shuffle_run{run_idx}_mixture_std_uS']:
                if col in df_out.columns:
                    n_nan = df_out[col].isna().sum()
                    if n_nan > 0:
                        print(f"  - {col}: {n_nan}/{len(df_out)} samples ({n_nan/len(df_out)*100:.1f}%)")
                        has_nans = True
        if not has_nans:
            print(f"  ✓ No NaN values in derived statistics")
        
        print(f"\nSummary statistics (mixture means from all runs):")
        mixture_cols = [f'shuffle_run{i}_mixture_mean_uS' for i in range(1, 6)]
        print(df_out[['y_measured_uS'] + mixture_cols].describe())


if __name__ == "__main__":
    main()
