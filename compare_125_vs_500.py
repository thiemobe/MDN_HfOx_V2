"""Deviation of mdn2 sample quantities between n=125 and n=500 (500 minus 125), paired by run index."""
import argparse
import os

import pandas as pd

import mdn_sample_report as r
import baseline_comparison as bc

parser = argparse.ArgumentParser()
parser.add_argument('--sample-idx', type=int, default=29)
parser.add_argument('--state', choices=bc.STATES, default='reset')
args = parser.parse_args()

_, a, _ = r.build_report(125, args.state, args.sample_idx)
_, b, _ = r.build_report(500, args.state, args.sample_idx)
d = b.values - a.values
dev = pd.DataFrame(d, columns=a.columns)
abs_dev = dev.abs()
out = pd.DataFrame({
    'mean_125': a.mean(), 'mean_500': b.mean(),
    'diff_mean (500-125)': dev.mean(), 'diff_std': dev.std(ddof=1),
    'abs_dev_mean': abs_dev.mean(), 'abs_dev_std': abs_dev.std(ddof=1),
    'rel_diff_of_means_%': 100 * (b.mean() - a.mean()) / a.mean().abs(),
})
pd.set_option('display.width', 250)
print(out.round(3).to_string())
path = os.path.join(bc.RESULTS_DIR, f'mdn2_deviation_125_vs_500_{args.state}_sample{args.sample_idx:04d}.csv')
out.rename_axis('quantity').to_csv(path)
print('[OK] Saved:', path)
