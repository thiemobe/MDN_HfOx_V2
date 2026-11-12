"""Scan SET and RESET test samples for bimodal mdn2 predictions that agree between n=125 and n=500 (sigma, pi, mu)."""
import numpy as np
import pandas as pd

import baseline_comparison as bc


def mean_params(n, state):
    d = np.load(bc.cache_path('mdn2', n))
    pi, mu, sg = (d[f'{state}_{k}'].astype(float) for k in ('pi', 'mu', 'sigma'))
    order = np.argsort(mu, axis=-1)
    pi, mu, sg = (np.take_along_axis(a, order, -1) for a in (pi, mu, sg))
    return pi.mean(0), mu.mean(0), sg.mean(0), pi.std(0, ddof=1)


_, y_all, masks = bc.load_test_data()
rows = []
for state in bc.STATES:
    p1, m1, s1, _ = mean_params(125, state)
    p2, m2, s2, _ = mean_params(500, state)
    y = y_all[masks[state]]
    for i in range(len(y)):
        bimodal = min(p1[i].min(), p2[i].min()) > 0.15 and min(m1[i, 1] - m1[i, 0], m2[i, 1] - m2[i, 0]) > 2 * max(s1[i].max(), s2[i].max())
        if not bimodal:
            continue
        rel_sigma = np.abs(s1[i] - s2[i]) / s2[i]
        rows.append(dict(state=state, idx=i, y=y[i], p1_125=p1[i, 0], p1_500=p2[i, 0],
                         mu1_125=m1[i, 0], mu1_500=m2[i, 0], mu2_125=m1[i, 1], mu2_500=m2[i, 1],
                         s1_125=s1[i, 0], s1_500=s2[i, 0], s2_125=s1[i, 1], s2_500=s2[i, 1],
                         sigma_err=rel_sigma.max(), pi_err=abs(p1[i, 0] - p2[i, 0]),
                         mu_err=np.abs(m1[i] - m2[i]).max()))
df = pd.DataFrame(rows)
df['score'] = df.sigma_err / 0.1 + df.pi_err / 0.05 + df.mu_err / 5
pd.set_option('display.width', 250)
print(len(df), 'bimodal candidates')
print(df.sort_values('score').head(12).round(3).to_string(index=False))
