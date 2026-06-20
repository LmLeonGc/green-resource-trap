import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from pathlib import Path

PROC = Path("data/processed")
OUTT = Path("outputs/tables"); OUTT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(PROC / "master_table.csv", index_col="iso3")
sa = df[df["group"] == "South America"].copy()

# Also load the meta-axes from the typology output
typ = pd.read_csv("outputs/tables/typology.csv", index_col="iso3")
sa["axis_dependence"] = typ["axis_dependence"]
sa["axis_capacity"]   = typ["axis_capacity"]

def spearman_ci(x, y, n_boot=5000, seed=42):
    """Spearman rho with bootstrap 95% CI. Returns (rho, p, lo, hi, n)."""
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    n = len(d)
    xv = d["x"].to_numpy()          # to numpy ONCE, outside the loop
    yv = d["y"].to_numpy()
    rho, p = spearmanr(xv, yv)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        s = rng.integers(0, n, size=n)        # fast integer resample
        xs, ys = xv[s], yv[s]
        if len(np.unique(xs)) < 3 or len(np.unique(ys)) < 3:
            continue
        r, _ = spearmanr(xs, ys)
        if not np.isnan(r):
            boots.append(r)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return rho, p, lo, hi, n

# Pairs that test the green resource trap mechanism
pairs = [
    ("f2_eci",   "f1_fossil", "Complexity vs fossil share"),
    ("f2_eci",   "f3_rents",  "Complexity vs resource rents"),
    ("f5_gov",   "f3_rents",  "Governance vs resource rents"),
    ("f5_gov",   "f1_fossil", "Governance vs fossil share"),
    ("f2_eci",   "f5_gov",    "Complexity vs governance"),
    ("axis_capacity", "axis_dependence", "Capacity vs dependence (meta-axes)"),
]

rows = []
for a, b, label in pairs:
    rho, p, lo, hi, n = spearman_ci(sa[a], sa[b])
    sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else "ns"
    rows.append({
        "relation": label, "var_x": a, "var_y": b,
        "spearman_rho": round(rho, 3), "p_value": round(p, 3),
        "ci_low": round(lo, 3), "ci_high": round(hi, 3),
        "n": n, "sig": sig,
    })

res = pd.DataFrame(rows)
print(res.to_string(index=False))
res.to_csv(OUTT / "correlations.csv", index=False)
print(f"\nSaved -> {OUTT/'correlations.csv'}")
# Report rho with CI in the paper; frame as associative (n=12).

# --- Robustness: drop Guyana (extreme outlier on dependence) ---
print("\n\n========== WITHOUT GUYANA ==========")
sa_ng = sa.drop("GUY")
rows_ng = []
for a, b, label in pairs:
    rho, p, lo, hi, n = spearman_ci(sa_ng[a], sa_ng[b])
    sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else "ns"
    rows_ng.append({"relation": label, "spearman_rho": round(rho,3),
                    "p_value": round(p,3), "ci_low": round(lo,3),
                    "ci_high": round(hi,3), "n": n, "sig": sig})
print(pd.DataFrame(rows_ng).to_string(index=False))