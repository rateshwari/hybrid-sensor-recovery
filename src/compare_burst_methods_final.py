"""Statistical comparisons for the burst-loss experiment."""

from pathlib import Path
from math import sqrt

import pandas as pd
from scipy.stats import t, ttest_ind, ttest_rel

INPUT = Path("results/tables/burst_recovery_results.csv")
OUTPUT = Path("results/tables/burst_pairwise_comparisons_final.csv")

df = pd.read_csv(INPUT)

RECOVERY = "source_packet_recovery_rate"

COMPARISONS = [
    ("Fountain (1.5x)", "No ECC", "welch"),
    ("Fountain (1.5x)", "Reed-Solomon (8+2)", "welch"),
    ("Fountain (2.0x)", "No ECC", "welch"),
    ("Fountain (2.0x)", "Reed-Solomon (8+2)", "welch"),
    ("Fountain (2.0x)", "Fountain (1.5x)", "paired"),
    ("Reed-Solomon (8+2)", "No ECC", "paired"),
]


def independent_comparison(a, b):
    """Welch test and CI for mean(a) - mean(b)."""
    n_a, n_b = len(a), len(b)
    var_a, var_b = a.var(ddof=1), b.var(ddof=1)

    difference = a.mean() - b.mean()
    se_squared = var_a / n_a + var_b / n_b
    se = sqrt(se_squared)

    df_num = se_squared ** 2
    df_den = (
        (var_a / n_a) ** 2 / (n_a - 1)
        + (var_b / n_b) ** 2 / (n_b - 1)
    )
    degrees_freedom = df_num / df_den
    margin = t.ppf(0.975, degrees_freedom) * se

    test = ttest_ind(a, b, equal_var=False)

    return difference, difference - margin, difference + margin, test.pvalue


def paired_comparison(a, b):
    """Paired test and CI for trial-wise differences a - b."""
    matched = pd.concat(
        [a.rename("a"), b.rename("b")],
        axis=1,
        join="inner",
    ).dropna()

    differences = matched["a"] - matched["b"]
    n = len(differences)

    if n < 2:
        raise ValueError("Need at least two matched trials.")

    difference = differences.mean()
    se = differences.std(ddof=1) / sqrt(n)
    margin = t.ppf(0.975, n - 1) * se

    test = ttest_rel(matched["a"], matched["b"])

    return (
        difference,
        difference - margin,
        difference + margin,
        test.pvalue,
        n,
    )


rows = []

for method_a, method_b, test_type in COMPARISONS:
    a = (
        df.loc[df["method"] == method_a, ["seed", RECOVERY]]
        .dropna()
        .set_index("seed")[RECOVERY]
    )
    b = (
        df.loc[df["method"] == method_b, ["seed", RECOVERY]]
        .dropna()
        .set_index("seed")[RECOVERY]
    )

    if test_type == "paired":
        difference, lower, upper, p_value, n = paired_comparison(a, b)
    else:
        difference, lower, upper, p_value = independent_comparison(a, b)
        n = min(len(a), len(b))

    rows.append({
        "method_a": method_a,
        "method_b": method_b,
        "test": "paired t-test" if test_type == "paired" else "Welch t-test",
        "trials_per_group_or_pairs": n,
        "mean_difference_percentage_points": difference * 100,
        "difference_ci_lower_pp": lower * 100,
        "difference_ci_upper_pp": upper * 100,
        "raw_p_value": p_value,
    })

result = pd.DataFrame(rows)

# Holm-Bonferroni adjustment, with no extra package required.
p_values = result["raw_p_value"].tolist()
order = sorted(range(len(p_values)), key=lambda i: p_values[i])

adjusted = [0.0] * len(p_values)
running_max = 0.0
m = len(p_values)

for rank, index in enumerate(order):
    candidate = min(1.0, (m - rank) * p_values[index])
    running_max = max(running_max, candidate)
    adjusted[index] = running_max

result["holm_adjusted_p_value"] = adjusted
result["significant_after_holm_0_05"] = (
    result["holm_adjusted_p_value"] < 0.05
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(OUTPUT, index=False)

print("=== FINAL BURST-LOSS PAIRWISE COMPARISONS ===")
print(result.to_string(index=False))
print(f"\nSaved to: {OUTPUT}")
