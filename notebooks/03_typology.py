import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, fcluster
from pathlib import Path

PROC = Path("data/processed")
OUTF = Path("outputs/figures"); OUTF.mkdir(parents=True, exist_ok=True)
OUTT = Path("outputs/tables");  OUTT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(PROC / "master_table.csv", index_col="iso3")
sa = df[df["group"] == "South America"].copy()
FRONTS = ["f1_fossil", "f2_eci", "f3_rents", "f5_gov"]

# z-score across the 12 SA countries
z = sa[FRONTS].apply(lambda c: (c - c.mean()) / c.std(ddof=0))
z.columns = [f"z_{c}" for c in FRONTS]

# Meta-axes
sa["axis_dependence"] = z["z_f1_fossil"] + z["z_f3_rents"]
sa["axis_capacity"]   = z["z_f2_eci"] + z["z_f5_gov"]

# --- Cut at ZERO (regional mean in z-space), declared a priori ---
TYPE_NAMES = {
    (True,  False): "Green resource trap",      # high dependence, low capacity
    (True,  True):  "Managed extraction",       # high dependence, high capacity
    (False, True):  "Diversifying",             # low dependence, high capacity
    (False, False): "Constrained transition",   # low dependence, low capacity
}
def classify(row):
    dep = row["axis_dependence"] > 0
    cap = row["axis_capacity"]   > 0
    return TYPE_NAMES[(dep, cap)]
sa["type"] = sa.apply(classify, axis=1)

# Border flag: countries within 0.5 z of either axis line
sa["border_case"] = (sa["axis_dependence"].abs() < 0.5) | (sa["axis_capacity"].abs() < 0.5)

# Robustness clustering
Z = linkage(z.values, method="ward")
sa["cluster_hc"] = fcluster(Z, t=4, criterion="maxclust")

cols = ["country","f1_fossil","f2_eci","f3_rents","f5_gov",
        "axis_dependence","axis_capacity","type","border_case","cluster_hc"]
print(sa[cols].round(2).sort_values("axis_dependence", ascending=False).to_string())
print("\n--- Type counts ---"); print(sa["type"].value_counts())
print("\n--- Border cases ---")
print(sa.loc[sa["border_case"], ["country","axis_dependence","axis_capacity","type"]].round(2).to_string())
print("\n--- Cross-tab type vs hierarchical cluster ---")
print(pd.crosstab(sa["type"], sa["cluster_hc"]))
sa.to_csv(OUTT / "typology.csv")

# Figure
fig, ax = plt.subplots(figsize=(9, 7))
ax.axvline(0, color="grey", lw=0.8, ls="--")
ax.axhline(0, color="grey", lw=0.8, ls="--")
colors = {
    "Green resource trap":   "#b2182b",
    "Managed extraction":    "#ef8a62",
    "Diversifying":          "#2166ac",
    "Constrained transition":"#67a9cf",
}
for t, g in sa.groupby("type"):
    ax.scatter(g["axis_dependence"], g["axis_capacity"], s=130,
               color=colors[t], label=t, edgecolor="black", zorder=3)
for iso3, r in sa.iterrows():
    style = "italic" if r["border_case"] else "normal"
    ax.annotate(iso3, (r["axis_dependence"], r["axis_capacity"]),
                xytext=(4,4), textcoords="offset points", fontsize=9, style=style)
ax.set_xlabel("Extractive dependence  (fossil share + resource rents, z)")
ax.set_ylabel("Transformation capacity  (complexity + governance, z)")
ax.set_title("South America's energy-transition typology\n(green resource trap framework)")
ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
fig.tight_layout()
fig.savefig(OUTF / "typology_2x2.png", dpi=200)
print(f"\nSaved -> {OUTF/'typology_2x2.png'}")