import pandas as pd
import numpy as np
from scipy.stats import kruskal
from pathlib import Path
import importlib.util as _ilu

# Reuse the validated OLADE loader
_spec = _ilu.spec_from_file_location("olade", Path(__file__).parent / "02_load_olade.py")
olade = _ilu.module_from_spec(_spec); _spec.loader.exec_module(olade)

PROC = Path("data/processed")
OUTT = Path("outputs/tables"); OUTT.mkdir(parents=True, exist_ok=True)
OUTF = Path("outputs/figures"); OUTF.mkdir(parents=True, exist_ok=True)

# ---------- F1 for 2010 and 2021 (same methodology) ----------
f1_2010 = olade.load_f1_fossil("Matriz_balance_energetico_2010.xlsx", year=2010)["f1_fossil"]
f1_2021 = olade.load_f1_fossil("Matriz_balance_energetico.xlsx", year=2021)["f1_fossil"]

# ---------- Outcome: change in fossil share 2010 -> 2021 ----------
# Negative = decarbonised the matrix (good trajectory); positive = stalled/worsened
delta = (f1_2021 - f1_2010).rename("delta_fossil")

# ---------- Merge with typology ----------
typ = pd.read_csv(OUTT / "typology.csv", index_col="iso3")
val = typ.join(f1_2010.rename("f1_fossil_2010")).join(f1_2021.rename("f1_fossil_2021")).join(delta)

cols = ["country","type","f1_fossil_2010","f1_fossil_2021","delta_fossil"]
print(val[cols].round(2).sort_values("delta_fossil").to_string())

# ---------- Trajectory by typology group ----------
print("\n--- Median fossil-share change by type (2010->2021) ---")
grp = val.groupby("type")["delta_fossil"].agg(["median","mean","count"]).round(2)
print(grp.to_string())

# ---------- Kruskal-Wallis: do trajectories differ across types? ----------
groups = [g["delta_fossil"].dropna().values for _, g in val.groupby("type")]
groups = [g for g in groups if len(g) > 0]
if len(groups) >= 2:
    H, p = kruskal(*groups)
    print(f"\nKruskal-Wallis across types: H={H:.2f}, p={p:.3f}")

val.to_csv(OUTT / "validation.csv")

# ---------- Figure: trajectory by type ----------
import matplotlib.pyplot as plt
order = ["Green resource trap","Managed extraction","Constrained transition","Diversifying"]
colors = {"Green resource trap":"#b2182b","Managed extraction":"#ef8a62",
          "Constrained transition":"#67a9cf","Diversifying":"#2166ac"}
fig, ax = plt.subplots(figsize=(9,6))
for t in order:
    sub = val[val["type"]==t]
    if sub.empty: continue
    ax.scatter([t]*len(sub), sub["delta_fossil"], s=120,
               color=colors[t], edgecolor="black", zorder=3)
    for iso3, r in sub.iterrows():
        ax.annotate(iso3, (t, r["delta_fossil"]), xytext=(6,0),
                    textcoords="offset points", fontsize=9, va="center")
ax.axhline(0, color="grey", lw=0.8, ls="--")
ax.set_ylabel("Change in fossil share of energy matrix,\n2010–2021 (percentage points)")
ax.set_title("Transition trajectory by typology group\n(below zero = decarbonising; above = stalling)")
plt.xticks(rotation=15, ha="right")
fig.tight_layout()
fig.savefig(OUTF / "trajectory_by_type.png", dpi=200)
print(f"\nSaved -> {OUTF/'trajectory_by_type.png'}")