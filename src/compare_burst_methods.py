
from pathlib import Path

import pandas as pd
from scipy.stats import ttest_ind
from scipy.stats import t
from math import sqrt

INPUT = Path("results/tables/burst_recovery_results.csv")
OUTPUT = Path("results/tables/burst_pairwise_comparisons.csv")

df = pd.read_csv(INPUT)

comparisons = [
    ("Fountain (1.5x)", "No ECC"),
    ("Fountain (1.5x)", "Reed-Solomon (8+2)"),
    ("Fountain (2.0x)", "No ECC"),
    ("Fountain (2.0x)", "Reed-Solomon (8+2)"),
    ("Fountain (2.0x)", "Fountain (1.5x)"),
    ("Reed-Solomon (8+2)", "No ECC"),
]

rows = []

for method_a, method_b in comparisons:
    a = df.loc[
        df["method"] == method_a,
        "source_packet_recovery_rate",
    ].dropna()
    b = df.loc[
        df["method"] == method_b,
        "source_packet_recovery_rate",
    ].dropna()

    difference = a.mean() - b.mean()

    # Welch's unequal-variance standard error and degrees of freedom.
    va, vb = a.var(ddof=1), b.var(ddof=1)
    se = sqrt(va / len(a) + vb / len(b))
    df_num = (va / len(a) + vb / len(b)) ** 2
    df_den = (
        (va / len(a)) ** 2 / (len(a) - 1)
        + (vb / len(b)) ** 2 / (len(b) - 1)
    )
    degrees_freedom = df_num / df_den
    margin = t.ppf(0.975, degrees_freedom) * se

    test = ttest_ind(a, b, equal_var=False)

    rows.append({
        "method_a": method_a,
        "method_b": method_b,
        "mean_difference_percentage_points": difference * 100,
        "difference_ci_lower_pp": (difference - margin) * 100,
        "difference_ci_upper_pp": (difference + margin) * 100,
        "welch_t_statistic": test.statistic,
        "p_value": test.pvalue,
        "trials_a": len(a),
        "trials_b": len(b),
    })

result = pd.DataFrame(rows)
result.to_csv(OUTPUT, index=False)
print(result.to_string(index=False))
print(f"\nSaved to: {OUTPUT}")
