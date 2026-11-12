"""
Per-sample report of the retrained 2-component MDN ('mdn2') from the cached baseline_comparison predictions:
mixture weights, means, sigmas, 95 % intervals of the full mixture and of each component, per run and as mean/std
over the runs.

Usage:  python mdn_sample_report.py --sample-idx 242 --state set --n 125 500
"""
import argparse
import os

import numpy as np
import pandas as pd
from scipy.stats import norm

import baseline_comparison as bc


def build_report(n, state, sample_idx, kind='mdn2'):
    _, y_all, masks = bc.load_test_data()
    y_true = float(y_all[masks[state]][sample_idx])
    data = np.load(bc.cache_path(kind, n))
    pi, mu, sigma = (data[f'{state}_{k}'][:, sample_idx].astype(float) for k in ('pi', 'mu', 'sigma'))
    order = np.argsort(mu, axis=-1)
    pi, mu, sigma = (np.take_along_axis(a, order, -1) for a in (pi, mu, sigma))
    n_runs, n_comp = pi.shape

    cols = {}
    for r in range(n_runs):
        lo, hi = bc.mixture_interval(pi[r], mu[r], sigma[r])
        cols.setdefault('mixture_q025', []).append(lo)
        cols.setdefault('mixture_q975', []).append(hi)
    cols['mixture_width'] = list(np.array(cols['mixture_q975']) - np.array(cols['mixture_q025']))
    cols['mixture_mean'] = list((pi * mu).sum(-1))
    cols['mixture_std'] = list(bc.mixture_std(pi, mu, sigma))
    for c in range(n_comp):
        cols[f'pi_{c + 1}'] = list(pi[:, c])
        cols[f'mu_{c + 1}'] = list(mu[:, c])
        cols[f'sigma_{c + 1}'] = list(sigma[:, c])
        cols[f'comp{c + 1}_q025'] = list(norm.ppf(0.025, mu[:, c], sigma[:, c]))
        cols[f'comp{c + 1}_q975'] = list(norm.ppf(0.975, mu[:, c], sigma[:, c]))

    per_run = pd.DataFrame(cols, index=[f'run{r + 1}' for r in range(n_runs)])
    summary = pd.DataFrame({'mean': per_run.mean(), 'std_over_runs': per_run.std(ddof=1)})
    return y_true, per_run, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample-idx', type=int, default=242)
    parser.add_argument('--state', choices=bc.STATES, default='set')
    parser.add_argument('--n', type=int, nargs='+', default=[125, 500])
    args = parser.parse_args()

    os.makedirs(bc.RESULTS_DIR, exist_ok=True)
    for n in args.n:
        y_true, per_run, summary = build_report(n, args.state, args.sample_idx)
        print(f"\n=== mdn2, n={n}, {args.state.upper()} sample {args.sample_idx} (measured {y_true:.2f} uS) ===")
        print(per_run.T.round(3).join(summary.round(3)).to_string())
        path = os.path.join(bc.RESULTS_DIR, f'mdn2_report_{args.state}_sample{args.sample_idx:04d}_n{n}.csv')
        per_run.T.join(summary).rename_axis('quantity').to_csv(path)
        print(f"[OK] Saved: {path}")


if __name__ == '__main__':
    main()
