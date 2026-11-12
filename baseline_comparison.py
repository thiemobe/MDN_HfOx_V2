r"""
Compare the MDN against simpler probabilistic regression baselines on the same data and protocol.

Models (all predict the conductance distribution p(G_after | state, G_before, V_applied)):
  mdn       2-component Gaussian mixture, CRPS loss  -> the stored MDN predictions from the paper
  hetero    heteroscedastic Gaussian (MDN with 1 component: mu(x), sigma(x)), CRPS loss
  hetero_deep  same as hetero but with 3 hidden layers (capacity control)
  mixconst  2-component mixture with learned pi(x), mu(x) but global learnable sigmas (one per component), CRPS loss
  mixshared 2-component mixture with learned pi(x), mu(x) and ONE global learnable sigma shared by both components, CRPS loss
  const      deterministic ANN (MSE loss) + one constant Gaussian sigma
            (CRPS-optimal on the validation residuals)
  quantile  quantile-regression network (100 non-crossing quantiles, pinball loss = discretised CRPS);
            non-parametric, so it can represent multimodal densities without a mixture parametrisation

Protocol (identical to training_and_validation.py / predictions_for_testset.py for the MDN):
  * training data: first 1.2*n rows of data/original_data.csv (n train + 20 % validation), n <= 500, i.e. only rows 0-599
  * test data: rows 600-1199 of the same file (all of them, outliers kept); scalers are fit on the n training rows only
  * 5 runs per n with shuffle seed n*1000 + run, weight-init seed 42
  * same hidden architecture (1 x 64, Mish, dropout 0.3), Adam lr 3e-3, batch 32, 800 epochs,
    early stopping (patience 200, min_delta 1e-4)
  * evaluation on the test rows, SET and RESET separately, metric = CRPS (uS)

NOTE: training_and_validation.py keeps `model.state_dict().copy()` as "best" checkpoint, which is a shallow
copy and therefore always tracks the live weights, so the stored paper MDN ('mdn') uses the weights at the
stopping epoch. All models trained here restore the weights of the best validation epoch (deep copy);
`--verify-protocol` uses the legacy behaviour to reproduce the paper MDN.

Usage:
    python baseline_comparison.py                      # train missing baselines, evaluate, plot
    python baseline_comparison.py --skip-training      # only evaluate/plot from cached predictions
    python baseline_comparison.py --verify-protocol    # check that this pipeline reproduces the stored MDN
    python baseline_comparison.py --sample-idx 180 --qual-n 500
    python baseline_comparison.py --device-csv data/d2d_original_data_1000/train_samples_dev_32_22_1000_samples_high_ratio.csv

check one specific device for crps and r2
python baseline_comparison.py --device-csv "data/d2d_original_data_1000/train_samples_dev_45_40_1000_samples_low_ratio.csv" --models mdn2
"""

import os
import re
import argparse
import copy
import random
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar
from scipy.special import ndtr
from scipy.stats import norm, gaussian_kde
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

from MDN import MDN
from MDN_loss import mdn_loss

# =========================
# Configuration
# =========================
TRAIN_CSV = 'data/original_data.csv'
N_POOL = 600  # rows 0..599 of TRAIN_CSV: train + validation pool; rows 600.. (all, outliers kept): test set
MDN_PREDICTIONS_DIR = 'predictions/final_predictions_shuffled_model_seperate_states_with_outliers'
CACHE_DIR = 'results/baseline_comparison/cache'
RESULTS_DIR = 'results/baseline_comparison'
FIGURES_DIR = 'figures/Baseline_comparison'
DEVICE_CSV = None
DEVICE_HOLDOUT_FRACTION = 0.2

N_RUNS = 5
VAL_RATIO = 0.2
WEIGHT_INIT_SEED = 42
PARAMS = dict(hidden_dim=64, hidden_layers=1, dropout=0.3, lr=3e-3, epochs=800, batch_size=32,
              patience=200, min_delta=1e-4)
N_QUANTILES = 100
TAUS = (np.arange(N_QUANTILES) + 0.5) / N_QUANTILES

BASELINES = ('hetero', 'hetero_deep', 'const', 'mixconst', 'mixshared', 'quantile', 'mdn2', 'mdn3', 'mdn4', 'mdn5')  # mdnK = retrained MDN with K components
MODELS_SIGMA_ABLATION = ('mdn2', 'const', 'mixshared', 'mixconst')  # learned sigma(x) vs. different constant-sigma variants
SIGMA_LABELS = {
    'mdn2': 'MDN, 2 Gaussians, $\\sigma(x)$',
    'const': '1 Gaussian, const. $\\sigma$',
    'mixshared': '2 Gaussians, shared const. $\\sigma$',
    'mixconst': '2 Gaussians, const. $\\sigma$ per component',
}
MODELS_VS_BASELINES = ('mdn2', 'hetero', 'const', 'mixconst', 'quantile')
MODELS_K_SWEEP = ('hetero', 'mdn2', 'mdn3', 'mdn4', 'mdn5')  # K = 1..5
K_LABELS = {'hetero': 'K=1', 'mdn2': 'K=2', 'mdn3': 'K=3', 'mdn4': 'K=4', 'mdn5': 'K=5'}
MODEL_LABELS = {
    'mdn': 'MDN, 2 Gaussians, $\\sigma(x)$ (paper)',
    'mdn2': 'MDN, 2 Gaussians, $\\sigma(x)$',
    'hetero': '1 Gaussian, $\\sigma(x)$',
    'hetero_deep': '1 Gaussian, $\\sigma(x)$ (3 hidden layers)',
    'mixconst': '2 Gaussians, const. $\\sigma$ per component',
    'const': '1 Gaussian, const. $\\sigma$',
    'mixshared': '2 Gaussians, shared const. $\\sigma$',
    'quantile': 'Quantile regression NN',
    'mdn3': 'MDN, 3 Gaussians, $\\sigma(x)$',
    'mdn4': 'MDN, 4 Gaussians, $\\sigma(x)$',
    'mdn5': 'MDN, 5 Gaussians, $\\sigma(x)$',
}
MODEL_COLORS = {'mdn': '#d62728', 'hetero': '#1f77b4', 'hetero_deep': '#17becf', 'mixconst': '#bcbd22', 'mixshared': '#e377c2', 'const': '#7f7f7f', 'quantile': '#2ca02c',
                'mdn2': '#d62728', 'mdn3': '#ff7f0e', 'mdn4': '#9467bd', 'mdn5': '#8c564b'}
STATES = ('set', 'reset')

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
# Data
# =========================
def load_training_arrays(n_total):
    """First n_total rows of the training CSV -> X=[state, G_before(uS), V], y=mean(G_after 1/5/10 s)(uS)."""
    if DEVICE_CSV is not None:
        X, y, train_indices, _ = load_device_arrays(DEVICE_CSV)
        if n_total > len(train_indices):
            raise ValueError(f"Requested {n_total} train+validation rows, but device training split has {len(train_indices)}.")
        selected = train_indices[:n_total]
        return X[selected], y[selected]

    if n_total > N_POOL:
        raise ValueError(f"Requested {n_total} train+validation rows, but the pool is limited to the first {N_POOL}.")
    return parse_original_rows(pd.read_csv(TRAIN_CSV, encoding='utf-8-sig').iloc[:n_total])


def parse_original_rows(df):
    state = np.where(df.iloc[:, 0].astype(str).str.strip().str.lower() == 'set', 1.0, 0.0)
    g_before = pd.to_numeric(df.iloc[:, 9], errors='coerce').to_numpy(float) * 1e6
    voltage = pd.to_numeric(df.iloc[:, 3], errors='coerce').to_numpy(float)
    y = pd.to_numeric(df.iloc[:, [11, 14, 17]].mean(axis=1), errors='coerce').to_numpy(float) * 1e6
    X = np.column_stack([state, g_before, voltage])
    assert np.all(np.isfinite(X)) and np.all(np.isfinite(y)), "NaNs in data"
    return X, y


def load_device_arrays(csv_path):
    """Load a device CSV and create one deterministic train-pool/holdout split."""
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    state_text = df['State'].astype(str).str.strip().str.lower().to_numpy()
    state = np.where(state_text == 'set', 1.0, 0.0)
    g_before = pd.to_numeric(df['G_before'], errors='coerce').to_numpy(float) * 1e6
    voltage = pd.to_numeric(df['V_applied'], errors='coerce').to_numpy(float)
    after_columns = [f'G_after_{seconds}s' for seconds in range(1, 11)]
    after_values = df[after_columns].apply(pd.to_numeric, errors='coerce').to_numpy(float)
    y = np.nanmean(after_values, axis=1) * 1e6
    X = np.column_stack([state, g_before, voltage])

    valid = np.all(np.isfinite(X), axis=1) & np.isfinite(y) & np.isin(state_text, ['set', 'reset'])
    X, y = X[valid], y[valid]
    if len(y) < 2:
        raise ValueError(f"Not enough valid device rows in {csv_path} to create a holdout split.")

    permutation = np.random.default_rng(WEIGHT_INIT_SEED).permutation(len(y))
    n_test = max(1, int(round(len(y) * DEVICE_HOLDOUT_FRACTION)))
    test_indices = permutation[:n_test]
    train_indices = permutation[n_test:]
    return X, y, train_indices, test_indices


def split_sizes(n):
    n_val = max(1, int(n * VAL_RATIO))
    return n_val, n + n_val


def scale_inputs(X, scaler):
    return np.column_stack([X[:, 0], scaler.transform(X[:, 1:])])


# =========================
# Models and losses
# =========================
class QuantileNet(nn.Module):
    """Same hidden stack as the MDN; outputs N_QUANTILES non-crossing quantiles (base + cumulative softplus)."""

    def __init__(self, input_dim, hidden_dim, n_quantiles, num_hidden_layers, dropout):
        super().__init__()
        self.hidden = MDN(input_dim, hidden_dim, 1, num_hidden_layers, dropout).hidden
        self.head = nn.Linear(hidden_dim, n_quantiles)
        with torch.no_grad():
            self.head.bias[1:] = float(np.log(np.expm1(0.02)))  # start with narrow, equally spaced quantiles

    def forward(self, x):
        out = self.head(self.hidden(x))
        base = out[:, :1]
        return torch.cat([base, base + torch.cumsum(F.softplus(out[:, 1:]), dim=1)], dim=1)


def pinball_crps(q, y, taus):
    """2 * mean pinball loss over the quantile levels = discretised CRPS of the quantile function."""
    diff = y.unsqueeze(1) - q
    return 2.0 * torch.maximum(taus * diff, (taus - 1.0) * diff).mean(dim=1).mean()


def fit_constant_sigma(residuals):
    """Single sigma minimising the mean Gaussian CRPS of held-out (validation) residuals, i.e. the same score used for
    evaluation and for training the other models. The mean prediction of the ANN is not changed by sigma."""
    r = np.abs(np.asarray(residuals, dtype=float))

    def mean_crps(log_sigma):
        s = np.exp(log_sigma)
        z = r / s
        return float(np.mean(s * (z * (2 * ndtr(z) - 1) + 2 * norm.pdf(z) - 1 / np.sqrt(np.pi))))

    res = minimize_scalar(mean_crps, bounds=(np.log(1e-3), np.log(1e2)), method='bounded')
    return float(np.exp(res.x))


class ConstSigmaMDN(MDN):
    """Gaussian mixture whose mu(x) and pi(x) are learned but whose component sigmas are global learnable scalars
    (one per component, or a single one shared by all components if shared_sigma)."""

    def __init__(self, input_dim, hidden_dim, n_components, num_hidden_layers, dropout, shared_sigma=False):
        super().__init__(input_dim, hidden_dim, n_components, num_hidden_layers, dropout)
        del self.sigma_head
        self.log_sigma = nn.Parameter(torch.zeros(1 if shared_sigma else n_components))

    def forward(self, x):
        h = self.hidden(x)
        pi = torch.softmax(self.pi_head(h), dim=-1)
        mu = self.mu_head(h)
        sigma = torch.clamp(torch.exp(self.log_sigma), min=1e-6).expand_as(mu)
        return pi, mu, sigma


def build_model(kind):
    p = PARAMS
    if kind == 'mdn':
        return MDN(3, p['hidden_dim'], 2, p['hidden_layers'], p['dropout'])
    if kind == 'hetero_deep':
        return MDN(3, p['hidden_dim'], 1, 3, p['dropout'])
    if kind == 'mixconst':
        return ConstSigmaMDN(3, p['hidden_dim'], 2, p['hidden_layers'], p['dropout'])
    if kind == 'mixshared':
        return ConstSigmaMDN(3, p['hidden_dim'], 2, p['hidden_layers'], p['dropout'], shared_sigma=True)
    if kind.startswith('mdn') and kind != 'mdn':
        return MDN(3, p['hidden_dim'], int(kind[3:]), p['hidden_layers'], p['dropout'])
    if kind in ('hetero', 'const'):
        return MDN(3, p['hidden_dim'], 1, p['hidden_layers'], p['dropout'])
    if kind == 'quantile':
        return QuantileNet(3, p['hidden_dim'], N_QUANTILES, p['hidden_layers'], p['dropout'])
    raise ValueError(kind)


def make_loss_fn(kind):
    taus = torch.tensor(TAUS, dtype=torch.float32)
    if kind in ('mdn', 'hetero', 'hetero_deep', 'mixconst', 'mixshared') or kind.startswith('mdn'):
        return lambda net, xb, yb: mdn_loss(*net(xb), yb, loss_type='crps')
    if kind == 'const':
        return lambda net, xb, yb: F.mse_loss(net(xb)[1][:, 0], yb)
    return lambda net, xb, yb: pinball_crps(net(xb), yb, taus)


def train_network(net, loss_fn, X_tr, y_tr, X_val, y_val, shuffle_seed, best_weights=True):
    """Training loop mirroring train_mdn_with_early_stopping. With best_weights the weights of the epoch with the
    lowest validation loss are restored; otherwise the weights at the stopping epoch are kept (legacy MDN behaviour)."""
    p = PARAMS
    gen = torch.Generator()
    gen.manual_seed(shuffle_seed)
    train_loader = DataLoader(TensorDataset(X_tr, y_tr), batch_size=p['batch_size'], shuffle=True, generator=gen)
    val_loader = DataLoader(TensorDataset(X_val, y_val), batch_size=64, shuffle=False)
    optimizer = torch.optim.Adam(net.parameters(), lr=p['lr'])

    best, wait, best_state = float('inf'), 0, None
    for _ in range(p['epochs']):
        net.train()
        for xb, yb in train_loader:
            optimizer.zero_grad()
            loss_fn(net, xb, yb).backward()
            optimizer.step()

        net.eval()
        total, count = 0.0, 0
        with torch.no_grad():
            for xb, yb in val_loader:
                total += loss_fn(net, xb, yb).item() * xb.shape[0]
                count += xb.shape[0]
        val_loss = total / count

        if val_loss < best - p['min_delta']:
            best, wait = val_loss, 0
            best_state = copy.deepcopy(net.state_dict())
        else:
            wait += 1
            if wait >= p['patience']:
                break
    if best_weights and best_state is not None:
        net.load_state_dict(best_state)
    return net


# =========================
# Fit one (model, n, run) and predict the test set
# =========================
def fit_and_predict(kind, n, run_idx, test_X, test_masks, best_weights=True, return_model=False):
    """Return {state: params} with predictions in uS for the SET/RESET test samples."""
    n_val, n_total = split_sizes(n)
    shuffle_seed = n * 1000 + run_idx

    X, y = load_training_arrays(n_total)
    np.random.seed(shuffle_seed)
    perm = np.random.permutation(len(X))
    X, y = X[perm], y[perm]
    scaler_X = StandardScaler().fit(X[:n, 1:])  # training rows only
    scaler_y = StandardScaler().fit(y[:n].reshape(-1, 1))
    X_s = scale_inputs(X, scaler_X)
    y_s = scaler_y.transform(y.reshape(-1, 1)).ravel()
    tensors = [torch.tensor(a, dtype=torch.float32) for a in
               (X_s[:n], y_s[:n], X_s[n:n + n_val], y_s[n:n + n_val])]

    torch.manual_seed(WEIGHT_INIT_SEED)
    np.random.seed(WEIGHT_INIT_SEED)
    random.seed(WEIGHT_INIT_SEED)
    net = build_model(kind)
    train_network(net, make_loss_fn(kind), *tensors, shuffle_seed, best_weights)
    net.eval()

    y_scale, y_mean = scaler_y.scale_[0], scaler_y.mean_[0]
    sigma_const = None
    if kind == 'const':
        with torch.no_grad():
            fit = net(tensors[2])[1][:, 0].numpy()
        sigma_const = fit_constant_sigma(fit - tensors[3].numpy())

    Xt = torch.tensor(scale_inputs(test_X, scaler_X), dtype=torch.float32)
    with torch.no_grad():
        out = net(Xt)

    result = {}
    for state, mask in test_masks.items():
        if kind == 'quantile':
            result[state] = {'q': out[mask].numpy() * y_scale + y_mean}
        else:
            pi, mu, sigma = (t[mask].numpy() for t in out)
            if kind == 'const':
                pi, sigma = np.ones_like(mu), np.full_like(mu, sigma_const)
            result[state] = {'pi': pi, 'mu': mu * y_scale + y_mean, 'sigma': sigma * y_scale}
    if return_model:
        return result, net, scaler_X, scaler_y
    return result


def load_test_data():
    if DEVICE_CSV is not None:
        X, y, _, test_indices = load_device_arrays(DEVICE_CSV)
        X, y = X[test_indices], y[test_indices]
        masks = {'set': X[:, 0] == 1.0, 'reset': X[:, 0] == 0.0}
        return X, y, masks

    X, y = parse_original_rows(pd.read_csv(TRAIN_CSV, encoding='utf-8-sig').iloc[N_POOL:])
    masks = {'set': X[:, 0] == 1.0, 'reset': X[:, 0] == 0.0}
    return X, y, masks


def cache_path(kind, n):
    return os.path.join(CACHE_DIR, f'{kind}_n{n}.npz')


def train_task(args):
    """Train all runs of one (model, n) and cache the predictions. Runs in a worker process."""
    kind, n, device_csv, task_cache_dir = args
    global DEVICE_CSV, CACHE_DIR
    DEVICE_CSV = device_csv
    CACHE_DIR = task_cache_dir
    torch.set_num_threads(1)
    test_X, _, masks = load_test_data()
    per_run = [fit_and_predict(kind, n, r, test_X, masks) for r in range(N_RUNS)]
    arrays = {f'{state}_{key}': np.stack([run[state][key] for run in per_run]).astype(np.float32)
              for state in STATES for key in per_run[0][state]}
    os.makedirs(CACHE_DIR, exist_ok=True)
    np.savez_compressed(cache_path(kind, n), **arrays)
    return kind, n


def discover_n_values():
    pattern = re.compile(r'_n(\d+)_set\.csv$', re.IGNORECASE)
    return sorted(int(m.group(1)) for fn in os.listdir(MDN_PREDICTIONS_DIR) if (m := pattern.search(fn)))


def train_all(n_values, models, workers, force, device_csv=None):
    tasks = [(k, n, device_csv, CACHE_DIR) for n in n_values for k in models
             if force or not os.path.exists(cache_path(k, n))]
    if not tasks:
        print("All baseline predictions are cached.")
        return
    tasks.sort(key=lambda t: -t[1])  # longest jobs first
    print(f"Training {len(tasks)} (model, n) jobs x {N_RUNS} runs on {workers} workers...")
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for done, (kind, n) in enumerate(pool.map(train_task, tasks), 1):
            print(f"  [{done}/{len(tasks)}] {kind} n={n}")


# =========================
# Metrics
# =========================
def crps_mixture(y, pi, mu, sigma):
    """Closed-form CRPS of Gaussian mixtures. y: (N,), pi/mu/sigma: (R, N, C) -> (R, N)."""
    sigma = np.maximum(sigma, 1e-6)
    yy = y[None, :, None]
    z = (yy - mu) / sigma
    first = (pi * (2 * sigma * norm.pdf(z) + (yy - mu) * (2 * ndtr(z) - 1))).sum(-1)
    d = mu[..., :, None] - mu[..., None, :]
    s = np.sqrt(sigma[..., :, None] ** 2 + sigma[..., None, :] ** 2)
    zz = d / s
    abs_diff = 2 * s * norm.pdf(zz) + d * (2 * ndtr(zz) - 1)
    second = 0.5 * (pi[..., :, None] * pi[..., None, :] * abs_diff).sum((-1, -2))
    return first - second


def crps_quantiles(y, q):
    """CRPS of a quantile function given at TAUS. y: (N,), q: (R, N, K) -> (R, N)."""
    q = np.sort(q, axis=-1)
    diff = y[None, :, None] - q
    return 2.0 * np.maximum(TAUS * diff, (TAUS - 1.0) * diff).mean(-1)


def load_mdn_predictions(n, state):
    pattern = re.compile(rf'_n{n}_{state}\.csv$', re.IGNORECASE)
    files = [fn for fn in os.listdir(MDN_PREDICTIONS_DIR) if pattern.search(fn)]
    if len(files) != 1:
        raise FileNotFoundError(f"Expected exactly one MDN prediction file for n={n} ({state}), found {files}")
    df = pd.read_csv(os.path.join(MDN_PREDICTIONS_DIR, files[0]), encoding='utf-8-sig')
    runs = sorted({int(m.group(1)) for c in df.columns if (m := re.match(r'^shuffle_run(\d+)_pi_1$', c))})
    stack = lambda name: np.stack([df[[f'shuffle_run{r}_{name}_{c}' for c in (1, 2)]].to_numpy(float)
                                   for r in runs])
    return df['y_measured_uS'].to_numpy(float), {'pi': stack('pi'), 'mu': stack('mu'), 'sigma': stack('sigma')}


def per_sample_crps(kind, n, state, y_true):
    """CRPS (R, N) of one model for one n and state."""
    if kind == 'mdn':
        y_csv, pred = load_mdn_predictions(n, state)
        if not np.allclose(y_csv, y_true):
            raise ValueError(f"MDN prediction file (n={n}, {state}) is not aligned with the test set")
        return crps_mixture(y_true, pred['pi'], pred['mu'], pred['sigma'])
    data = np.load(cache_path(kind, n))
    if kind == 'quantile':
        return crps_quantiles(y_true, data[f'{state}_q'].astype(float))
    return crps_mixture(y_true, *(data[f'{state}_{k}'].astype(float) for k in ('pi', 'mu', 'sigma')))


def per_sample_mean(kind, n, state):
    """Predicted mean (R, N) in uS of one model for one n and state (mixture mean = sum(pi * mu))."""
    if kind == 'mdn':
        _, pred = load_mdn_predictions(n, state)
    else:
        data = np.load(cache_path(kind, n))
        if kind == 'quantile':
            return data[f'{state}_q'].astype(float).mean(-1)
        pred = {k: data[f'{state}_{k}'].astype(float) for k in ('pi', 'mu')}
    return (pred['pi'] * pred['mu']).sum(-1)


def r_squared(y_true, y_pred):
    """R^2 = 1 - SS_res / SS_tot (same definition as compute_r_squared.py)."""
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    return np.nan if ss_tot == 0 else 1 - np.sum((y_true - y_pred) ** 2) / ss_tot


def summarize(n_values, models):
    _, y_all, masks = load_test_data()
    y_pooled = np.concatenate([y_all[masks[s]] for s in STATES])
    rows = []
    for n in n_values:
        for kind in models:
            crps = {s: per_sample_crps(kind, n, s, y_all[masks[s]]) for s in STATES}
            pred_means = {s: per_sample_mean(kind, n, s) for s in STATES}
            means = np.concatenate([pred_means[s] for s in STATES], axis=1)
            # R^2 per run (pooled over SET and RESET, and for each state separately), then mean/std over runs
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
# Plots
# =========================
def plot_crps_vs_n(summary, tag, models, output_dir, suffix='', labels=MODEL_LABELS, metric='crps', legend_below=True,
                   inset_range=None, inset_rect=(0.5, 0.5, 0.42, 0.42)):
    mean_col, std_col = (('crps_mean', 'crps_std_over_runs') if metric == 'crps'
                         else ('r2_mean', 'r2_std_over_runs'))
    fig, ax = plt.subplots(1, 1, figsize=(3, 3))
    for kind in models:
        d = summary[(summary.model == kind) & (summary.state == tag)].sort_values('n_train')
        color = MODEL_COLORS[kind]
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
            color = MODEL_COLORS[kind]
            axins.plot(d.n_train, d[mean_col], 'o-', markersize=2.5, color=color, linewidth=1)
            axins.fill_between(d.n_train, d[mean_col] - d[std_col], d[mean_col] + d[std_col],
                               color=color, alpha=0.15, linewidth=0)
            ys += [(d[mean_col] - d[std_col]).min(), (d[mean_col] + d[std_col]).max()]
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
    path = os.path.join(output_dir, f'{metric}_vs_n_{tag}{suffix}.png')
    fig.savefig(path, dpi=100, bbox_inches='tight')
    fig.savefig(path.replace('.png', '.svg'), bbox_inches='tight')
    plt.close(fig)
    print(f"[OK] Saved: {path}")


def mixture_interval(pi, mu, sigma, levels=(0.025, 0.975), n_grid=4096):
    """Equal-tailed interval of a 1D Gaussian mixture from its CDF (same method as compute_mixture_quantiles)."""
    sigma = np.maximum(sigma, 1e-12)
    grid = np.linspace((mu - 8 * sigma).min(), (mu + 8 * sigma).max(), n_grid)
    cdf = np.maximum.accumulate(np.clip((pi * norm.cdf(grid[:, None], mu, sigma)).sum(-1), 0, 1))
    return tuple(float(np.interp(q, cdf, grid)) for q in levels)


def predictive_interval_table(sample_idx, state, n, models, output_dir):
    """95 % predictive interval of one test sample for every model/run; mean over runs saved to CSV."""
    _, y_all, masks = load_test_data()
    y_true = y_all[masks[state]][sample_idx]
    rows = []
    for kind in models:
        data = np.load(cache_path(kind, n))
        if kind == 'quantile':
            q = np.sort(data[f'{state}_q'][:, sample_idx].astype(float), axis=-1)
            i_lo, i_hi = np.argmin(np.abs(TAUS - 0.025)), np.argmin(np.abs(TAUS - 0.975))
            bounds = np.stack([q[:, i_lo], q[:, i_hi]], axis=1)
        else:
            p = {k: data[f'{state}_{k}'][:, sample_idx].astype(float) for k in ('pi', 'mu', 'sigma')}
            bounds = np.array([mixture_interval(p['pi'][r], p['mu'][r], p['sigma'][r]) for r in range(len(p['pi']))])
        rows.append({'model': kind, 'state': state, 'sample_idx': sample_idx, 'n_train': n, 'y_true_uS': y_true,
                     **{f'run{r + 1}_{name}': bounds[r, j] for r in range(len(bounds))
                        for j, name in enumerate(('q025', 'q975'))},
                     'q025_mean': bounds[:, 0].mean(), 'q975_mean': bounds[:, 1].mean(),
                     'width_mean': (bounds[:, 1] - bounds[:, 0]).mean(),
                     'truth_inside_runs': int(((y_true >= bounds[:, 0]) & (y_true <= bounds[:, 1])).sum())})
    df = pd.DataFrame(rows)
    path = os.path.join(output_dir, f'predictive_interval_{state}_sample{sample_idx:04d}_n{n}.csv')
    df.to_csv(path, index=False)
    print(f"[OK] Saved: {path}")
    print(df[['model', 'q025_mean', 'q975_mean', 'width_mean', 'truth_inside_runs']].round(2).to_string(index=False))


def ensemble_pdf(kind, n, state, sample_idx, x):
    """Run-averaged predictive density of one test sample on grid x."""
    if kind == 'mdn':
        _, p = load_mdn_predictions(n, state)
        p = {k: v[:, sample_idx] for k, v in p.items()}
    else:
        data = np.load(cache_path(kind, n))
        if kind == 'quantile':
            q = np.sort(data[f'{state}_q'][:, sample_idx].astype(float), axis=-1)
            # visualisation only: the equally likely quantile values are smoothed with a Gaussian KDE
            return np.mean([gaussian_kde(r, bw_method=0.12)(x) for r in q], axis=0)
        p = {k: data[f'{state}_{k}'][:, sample_idx].astype(float) for k in ('pi', 'mu', 'sigma')}
    pdfs = (p['pi'][:, :, None] * norm.pdf(x[None, None, :], p['mu'][:, :, None],
                                          np.maximum(p['sigma'], 1e-6)[:, :, None])).sum(1)
    return pdfs.mean(0)


def plot_qualitative(sample_idx, state, n_list, models, output_dir, suffix='', labels=MODEL_LABELS, legend_below=True):
    _, y_all, masks = load_test_data()
    y_true = y_all[masks[state]][sample_idx]
    x = np.linspace(0, 150, 600)

    fig, axes = plt.subplots(1, len(n_list), figsize=(3 * len(n_list), 3), sharey=True, squeeze=False)
    for ax, n in zip(axes[0], n_list):
        for kind in models:
            ax.plot(x, ensemble_pdf(kind, n, state, sample_idx, x), color=MODEL_COLORS[kind], linewidth=1.8,
                    label=labels[kind])
        ax.axvline(y_true, color='k', linestyle='--', linewidth=1.5, label=f'GT: {y_true:.1f} \u00b5S')
        ax.set_xlim(0, 150)
        ax.set_xlabel('Conductance (\u00b5S)')
        ax.set_title(f'n = {n} training samples')
        ax.grid(True, alpha=0.3)
    axes[0][0].set_ylabel('Probability Density')
    if legend_below:
        axes[0][0].legend(loc='upper center', bbox_to_anchor=(0.5, -0.28), frameon=False)
    else:
        axes[0][0].legend(loc='best')
    path = os.path.join(output_dir, f'qualitative_{state.upper()}_sample{sample_idx:04d}{suffix}.png')
    fig.savefig(path, dpi=100, bbox_inches='tight')
    fig.savefig(path.replace('.png', '.svg'), bbox_inches='tight')
    plt.close(fig)
    print(f"[OK] Saved: {path}")


def mixture_std(pi, mu, sigma):
    """Standard deviation of a Gaussian mixture, (..., C) -> (...)."""
    mean = (pi * mu).sum(-1)
    return np.sqrt(np.maximum((pi * (sigma ** 2 + mu ** 2)).sum(-1) - mean ** 2, 0.0))


def plot_sigma_variation(n, output_dir, kind='mdn'):
    """Show that the predicted spread of the MDN depends on the input: predictive std of every test sample vs. G_before,
    coloured by the applied voltage (mean over the shuffle runs), for SET and RESET."""
    X, _, masks = load_test_data()
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.2), sharey=True)
    scatter = None
    for ax, state in zip(axes, STATES):
        if kind == 'mdn':
            _, p = load_mdn_predictions(n, state)
        else:
            data = np.load(cache_path(kind, n))
            p = {k: data[f'{state}_{k}'].astype(float) for k in ('pi', 'mu', 'sigma')}
        std = mixture_std(p['pi'], p['mu'], p['sigma']).mean(0)
        g_before, volt = X[masks[state], 1], X[masks[state], 2]
        scatter = ax.scatter(g_before, std, c=volt, cmap='viridis', s=14, alpha=0.85, linewidths=0)
        lo, hi = np.percentile(std, [5, 95])
        ax.set_title(f'{state.upper()}  (5-95 %: {lo:.1f}-{hi:.1f} \u00b5S, x{hi / lo:.1f})', fontsize=12)
        ax.set_xlabel('Conductance before pulse (\u00b5S)')
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel('Predicted std $\\sigma_{pred}$ (\u00b5S)')
    fig.colorbar(scatter, ax=axes, label='Applied voltage (V)', pad=0.02)
    path = os.path.join(output_dir, f'sigma_variation_n{n}_{kind}.png')
    fig.savefig(path, dpi=100, bbox_inches='tight')
    fig.savefig(path.replace('.png', '.svg'), bbox_inches='tight')
    plt.close(fig)
    print(f"[OK] Saved: {path}")


def paired_crps_differences(n_values, ref='mdn2', others=('const', 'mixshared', 'mixconst'), n_boot=2000, seed=0):
    """Per-sample paired CRPS difference d_i = CRPS_other(i) - CRPS_ref(i) (positive = ref is better), SET and RESET
    pooled and averaged over the training runs, with a percentile bootstrap CI over the test samples."""
    _, y_all, masks = load_test_data()
    rng = np.random.default_rng(seed)
    rows = []
    for n in n_values:
        per_sample = {k: np.concatenate([per_sample_crps(k, n, s, y_all[masks[s]]) for s in STATES], axis=1).mean(0)
                      for k in (ref, *others)}
        idx = rng.integers(0, len(per_sample[ref]), size=(n_boot, len(per_sample[ref])))
        for k in others:
            d = per_sample[k] - per_sample[ref]
            boot = d[idx].mean(1)
            lo, hi = np.percentile(boot, [2.5, 97.5])
            rows.append({'ref': ref, 'other': k, 'n_train': n, 'mean_diff': d.mean(), 'ci_low': lo, 'ci_high': hi,
                         'frac_ref_better': float((d > 0).mean()), 'n_test': len(d)})
    return pd.DataFrame(rows)


def plot_paired_differences(diffs, output_dir, labels=SIGMA_LABELS):
    fig, ax = plt.subplots(1, 1, figsize=(3, 3))
    for k in diffs.other.unique():
        d = diffs[diffs.other == k].sort_values('n_train')
        ax.plot(d.n_train, d.mean_diff, 'o-', markersize=4, color=MODEL_COLORS[k], linewidth=1.5, label=labels[k])
        ax.fill_between(d.n_train, d.ci_low, d.ci_high, color=MODEL_COLORS[k], alpha=0.2, linewidth=0)
    ax.axhline(0, color='k', linewidth=1)
    ax.set_xscale('log')
    ax.set_xlabel('Training Samples')
    ax.set_ylabel('$\\Delta$CRPS (\u00b5S)')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.28), frameon=False)
    path = os.path.join(output_dir, 'paired_crps_difference_vs_mdn.png')
    fig.savefig(path, dpi=100, bbox_inches='tight')
    fig.savefig(path.replace('.png', '.svg'), bbox_inches='tight')
    plt.close(fig)
    print(f"[OK] Saved: {path}")


# =========================
# Protocol check
# =========================
def verify_protocol(n=200):
    """Retrain run 1 of the MDN with this script's pipeline and compare with the stored MDN predictions."""
    test_X, y_all, masks = load_test_data()
    mine = fit_and_predict('mdn', n, 0, test_X, masks, best_weights=False)
    print(f"Protocol check: retrained MDN n={n}, run 1 vs. stored predictions")
    for state in STATES:
        y = y_all[masks[state]]
        _, stored = load_mdn_predictions(n, state)
        c_mine = crps_mixture(y, mine[state]['pi'][None], mine[state]['mu'][None], mine[state]['sigma'][None])[0]
        c_stored = crps_mixture(y, stored['pi'][:1], stored['mu'][:1], stored['sigma'][:1])[0]
        print(f"  {state.upper():5s} mean CRPS  retrained: {c_mine.mean():.4f}   stored: {c_stored.mean():.4f}   "
              f"mean |diff per sample|: {np.abs(c_mine - c_stored).mean():.4f}")

    from evaluate_predictions_crps import compute_crps_mixture
    y = y_all[masks['set']][:5]
    _, stored = load_mdn_predictions(n, 'set')
    closed = crps_mixture(y, stored['pi'][:1, :5], stored['mu'][:1, :5], stored['sigma'][:1, :5])[0]
    numeric = [compute_crps_mixture(y[i], stored['pi'][0, i], stored['mu'][0, i], stored['sigma'][0, i])
               for i in range(5)]
    print(f"  closed-form vs. numerical CRPS (5 SET samples): max |diff| = {np.max(np.abs(closed - numeric)):.2e}")

    q = norm.ppf(TAUS)[None, None, :] * 7.0 + 30.0
    exact = crps_mixture(np.array([40.0]), np.ones((1, 1, 1)), np.full((1, 1, 1), 30.0), np.full((1, 1, 1), 7.0))
    print(f"  quantile-CRPS discretisation error for a Gaussian: "
          f"{abs(crps_quantiles(np.array([40.0]), q)[0, 0] - exact[0, 0]):.2e} uS")


# =========================
# Main
# =========================
def main():
    parser = argparse.ArgumentParser(description="Compare the MDN with simpler probabilistic baselines (CRPS)")
    parser.add_argument('--models', nargs='+', choices=BASELINES, default=list(BASELINES),
                        help='Baselines to train/evaluate (default: all)')
    parser.add_argument('--n-values', type=int, nargs='+', default=None,
                        help='Training-set sizes (default: all sizes with stored MDN predictions)')
    parser.add_argument('--workers', type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument('--skip-training', action='store_true', help='Only evaluate cached predictions')
    parser.add_argument('--force-retrain', action='store_true', help='Retrain even if cached predictions exist')
    parser.add_argument('--verify-protocol', action='store_true',
                        help='Retrain one stored MDN with this pipeline and compare, then exit')
    parser.add_argument('--device-csv', type=str, default=None,
                        help='Use a device CSV for training and a deterministic 20%% holdout from that same CSV for evaluation')
    parser.add_argument('--sample-idx', type=int, nargs='+', default=None,
                        help='Test sample(s) (index within the state) for the qualitative plot')
    parser.add_argument('--state', choices=STATES, default='set')
    parser.add_argument('--qual-n', type=int, nargs='+', default=[500],
                        help='Training-set sizes shown in the qualitative plot')
    args = parser.parse_args()

    if args.verify_protocol:
        verify_protocol()
        return

    global DEVICE_CSV, CACHE_DIR, RESULTS_DIR, FIGURES_DIR
    if args.device_csv:
        DEVICE_CSV = os.path.abspath(args.device_csv)
        if not os.path.isfile(DEVICE_CSV):
            parser.error(f'Device CSV not found: {DEVICE_CSV}')
        dataset_match = re.search(r'dev_(\d+_\d+)', os.path.basename(DEVICE_CSV))
        output_tag = f'device_{dataset_match.group(1)}' if dataset_match else os.path.splitext(os.path.basename(DEVICE_CSV))[0]
        output_root = os.path.join('results', 'baseline_comparison', output_tag)
        CACHE_DIR = os.path.join(output_root, 'cache')
        RESULTS_DIR = output_root
        FIGURES_DIR = os.path.join('figures', 'Baseline_comparison', output_tag)
        print(f"Device training/evaluation CSV: {DEVICE_CSV}")
        print(f"Evaluation split: deterministic {DEVICE_HOLDOUT_FRACTION:.0%} holdout from the same device CSV")

    if args.sample_idx is None:
        args.sample_idx = [0] if DEVICE_CSV is not None else [242]  # 242 = old SET sample 180 (row 1088 of original_data.csv)

    n_values = args.n_values or discover_n_values()
    if not args.skip_training:
        train_all(n_values, args.models, args.workers, args.force_retrain, device_csv=DEVICE_CSV)

    models = [k for k in args.models if k != 'hetero_deep']  # capacity-control model is not evaluated/plotted
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    summary = summarize(n_values, models)
    summary_path = os.path.join(RESULTS_DIR, 'crps_summary.csv')
    summary.to_csv(summary_path, index=False)
    print(f"[OK] Saved: {summary_path}")
    r2_path = os.path.join(RESULTS_DIR, 'r2_summary.csv')
    (summary[['model', 'n_train', 'state', 'r2_mean', 'r2_std_over_runs', 'n_test']]
     .sort_values(['model', 'state', 'n_train']).to_csv(r2_path, index=False))
    print(f"[OK] Saved: {r2_path}")

    vs_baselines = [k for k in MODELS_VS_BASELINES if k in models]
    k_sweep = [k for k in MODELS_K_SWEEP if k in models]
    sigma_ablation = [k for k in MODELS_SIGMA_ABLATION if k in models]
    shared_sigma_ablation = [k for k in ('mdn2', 'mixshared') if k in models]
    shared_vs_baselines = [k for k in ('mdn2', 'hetero', 'mixshared', 'quantile') if k in models]
    shared_qual_labels = {**SIGMA_LABELS, 'mixshared': '2 Gaussians, const. $\\sigma$'}
    for tag in ('SET', 'RESET', 'SET_and_RESET'):
        plot_crps_vs_n(summary, tag, models, FIGURES_DIR)
        plot_crps_vs_n(summary, tag, vs_baselines, FIGURES_DIR, suffix='_mdn_vs_baselines')
        plot_crps_vs_n(summary, tag, k_sweep, FIGURES_DIR, suffix='_k_components', labels=K_LABELS)
        plot_crps_vs_n(summary, tag, k_sweep, FIGURES_DIR, suffix='_k_components_inset', labels=K_LABELS,
                       inset_range=(100, 500))
        plot_crps_vs_n(summary, tag, sigma_ablation, FIGURES_DIR, suffix='_sigma_ablation', labels=SIGMA_LABELS,
                       legend_below=True)
        plot_crps_vs_n(summary, tag, sigma_ablation, FIGURES_DIR, suffix='_sigma_ablation_inset', labels=SIGMA_LABELS,
                       legend_below=True, inset_range=(100, 500))
        if 'quantile' in models:
            qr_ablation = shared_sigma_ablation if tag == 'SET_and_RESET' else sigma_ablation
            plot_crps_vs_n(summary, tag, qr_ablation + ['quantile'], FIGURES_DIR,
                           suffix='_sigma_ablation_qr_inset', labels=MODEL_LABELS | SIGMA_LABELS,
                           legend_below=True, inset_range=(100, 500))
    for group, suffix, labels in ((models, '', MODEL_LABELS), (vs_baselines, '_mdn_vs_baselines', MODEL_LABELS),
                                  (k_sweep, '_k_components', K_LABELS),
                                  (sigma_ablation, '_sigma_ablation', SIGMA_LABELS)):
        plot_crps_vs_n(summary, 'SET_and_RESET', group, FIGURES_DIR, suffix=suffix, labels=labels, metric='r2',
                       legend_below=suffix == '_sigma_ablation')
    plot_crps_vs_n(summary, 'SET_and_RESET', k_sweep, FIGURES_DIR, suffix='_k_components_inset', labels=K_LABELS,
                   metric='r2', inset_range=(100, 500), inset_rect=(0.5, 0.08, 0.42, 0.42))
    plot_crps_vs_n(summary, 'SET_and_RESET', sigma_ablation, FIGURES_DIR, suffix='_sigma_ablation_inset',
                   labels=SIGMA_LABELS, metric='r2', legend_below=True, inset_range=(100, 500),
                   inset_rect=(0.5, 0.08, 0.42, 0.42))
    if 'quantile' in models:
        plot_crps_vs_n(summary, 'SET_and_RESET', shared_sigma_ablation + ['quantile'], FIGURES_DIR,
                       suffix='_sigma_ablation_qr_inset', labels=MODEL_LABELS | SIGMA_LABELS, metric='r2',
                       legend_below=True, inset_range=(100, 500), inset_rect=(0.5, 0.08, 0.42, 0.42))
    for tag in ('SET', 'RESET'):
        for group, suffix, labels in ((models, '', MODEL_LABELS), (vs_baselines, '_mdn_vs_baselines', MODEL_LABELS),
                                      (k_sweep, '_k_components', K_LABELS),
                                      (sigma_ablation, '_sigma_ablation', SIGMA_LABELS)):
            plot_crps_vs_n(summary, tag, group, FIGURES_DIR, suffix=suffix, labels=labels, metric='r2',
                           legend_below=suffix == '_sigma_ablation')
        plot_crps_vs_n(summary, tag, k_sweep, FIGURES_DIR, suffix='_k_components_inset', labels=K_LABELS,
                       metric='r2', inset_range=(100, 500), inset_rect=(0.5, 0.08, 0.42, 0.42))
        plot_crps_vs_n(summary, tag, sigma_ablation, FIGURES_DIR, suffix='_sigma_ablation_inset',
                       labels=SIGMA_LABELS, metric='r2', legend_below=True, inset_range=(100, 500),
                       inset_rect=(0.5, 0.08, 0.42, 0.42))
        if 'quantile' in models:
            plot_crps_vs_n(summary, tag, sigma_ablation + ['quantile'], FIGURES_DIR,
                           suffix='_sigma_ablation_qr_inset', labels=MODEL_LABELS | SIGMA_LABELS, metric='r2',
                           legend_below=True, inset_range=(100, 500), inset_rect=(0.5, 0.08, 0.42, 0.42))
    qual_n = [n for n in args.qual_n if n in n_values]
    for sample_idx in args.sample_idx:
        for n in qual_n:
            predictive_interval_table(sample_idx, args.state, n, models, RESULTS_DIR)
        plot_qualitative(sample_idx, args.state, qual_n, models, FIGURES_DIR)
        selected_baselines = shared_vs_baselines if args.state == 'set' and sample_idx == 242 else vs_baselines
        plot_qualitative(sample_idx, args.state, qual_n, selected_baselines, FIGURES_DIR, suffix='_mdn_vs_baselines')
        plot_qualitative(sample_idx, args.state, qual_n, k_sweep, FIGURES_DIR, suffix='_k_components',
                         labels=K_LABELS)
        plot_qualitative(sample_idx, args.state, qual_n, sigma_ablation, FIGURES_DIR, suffix='_sigma_ablation',
                         labels=SIGMA_LABELS, legend_below=True)
        if args.state == 'set' and sample_idx == 242:
            plot_qualitative(sample_idx, args.state, qual_n, shared_sigma_ablation, FIGURES_DIR,
                             suffix='_sigma_ablation_shared_only', labels=shared_qual_labels, legend_below=True)
    for n in qual_n:
        plot_sigma_variation(n, FIGURES_DIR, kind='mdn2')

    if 'mdn2' in models:
        others = [k for k in ('const', 'mixshared', 'mixconst') if k in models]
        if others:
            diffs = paired_crps_differences(n_values, others=others)
            diffs_path = os.path.join(RESULTS_DIR, 'paired_crps_differences.csv')
            diffs.to_csv(diffs_path, index=False)
            print(f"[OK] Saved: {diffs_path}")
            plot_paired_differences(diffs, FIGURES_DIR)

    table = summary[summary.state == 'SET_and_RESET'].pivot(index='n_train', columns='model', values='crps_mean')
    print("\nMean CRPS (uS), SET and RESET pooled, mean over 5 runs:")
    print(table[models].round(2).to_string())


if __name__ == "__main__":
    main()
