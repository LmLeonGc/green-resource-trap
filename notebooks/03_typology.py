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

# Figure — same parameters as notebooks 08-11: DejaVu Sans, grey #3b3b3b,
# thin frame, matched axis text size, 600 dpi + SVG. No legend: each
# quadrant is named directly in its own corner instead (colored to match
# its points), so identity doesn't rely on a separate color key.
GREY = "#3b3b3b"
FS_TICK, FS_LABEL = 13, 14
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": "#222222"})

fig, ax = plt.subplots(figsize=(9, 7), facecolor="white")
ax.axvline(0, color=GREY, lw=0.8, ls="--", zorder=1)
ax.axhline(0, color=GREY, lw=0.8, ls="--", zorder=1)
colors = {
    "Green resource trap":   "#b2182b",
    "Managed extraction":    "#ef8a62",
    "Diversifying":          "#2166ac",
    "Constrained transition":"#67a9cf",
}
for t, g in sa.groupby("type"):
    ax.scatter(g["axis_dependence"], g["axis_capacity"], s=130,
               color=colors[t], edgecolor="black", zorder=3)
# extra margin (default autoscale is ~5%): the outward-pushed country labels
# on the extremal points (Paraguay, Guyana) need more room than that on the
# x side specifically, or their label touches the left/right plot border
ax.margins(x=0.17, y=0.10)
# Argentina/Brazil/Colombia sit close together in the upper-left quadrant;
# pushed below-left instead of above-left, so their labels read as a
# staircase under the points rather than crowding above them
BELOW_LEFT = {"argentina", "brazil", "colombia"}
# Paraguay is the leftmost point (closest to the border even with the
# extra margin above) — centered straight below its marker instead of
# diagonal, so its label doesn't need any extra horizontal room
CENTERED_BELOW = {"paraguay"}
for iso3, r in sa.iterrows():
    dep, cap = r["axis_dependence"], r["axis_capacity"]
    name = str(r["country"]).strip().lower()
    # push the label diagonally AWAY from the origin (the dashed quadrant
    # lines cross at 0,0), not just up-right — so it clears whichever line
    # the point sits closest to, on either side, instead of risking a
    # label that straddles one of them. Kept modest: in a tight cluster,
    # pushing labels too far makes it ambiguous which point each belongs to.
    dx, dy = (6 if dep >= 0 else -6), (5 if cap >= 0 else -5)
    ha, va = ("left" if dx > 0 else "right"), ("bottom" if dy > 0 else "top")
    if name in BELOW_LEFT:
        dx, dy = -6, -5
    elif name in CENTERED_BELOW:
        dx, dy, ha, va = 0, -10, "center", "top"
    ax.annotate(str(r["country"]).title(), (dep, cap),
                xytext=(dx, dy), textcoords="offset points", fontsize=11,
                ha=ha, va=va, color=GREY, fontweight="bold", zorder=4)

# quadrant name, bottom-anchored in its own quadrant: the two left-side
# names bottom-left aligned, the two right-side names bottom-right aligned
# (data coords, so it holds position regardless of the data's actual range)
QUADRANT_FS = FS_LABEL - 1
xmin, xmax = ax.get_xlim()
ymin, ymax = ax.get_ylim()
pad_x = (xmax - xmin) * 0.02
pad_y = (ymax - ymin) * 0.02
quadrant_pos = {
    "Diversifying":           (xmin + pad_x, 0 + pad_y,    "left",  "bottom"),
    "Managed extraction":     (xmax - pad_x, 0 + pad_y,    "right", "bottom"),
    "Constrained transition": (xmin + pad_x, ymin + pad_y, "left",  "bottom"),
    "Green resource trap":    (xmax - pad_x, ymin + pad_y, "right", "bottom"),
}
for t, (x, y, ha, va) in quadrant_pos.items():
    ax.text(x, y, t, ha=ha, va=va,
            fontsize=QUADRANT_FS, fontweight="bold", color=colors[t], zorder=5)

ax.set_xlabel("Extractive dependence  (fossil share + resource rents, z)",
              fontsize=FS_LABEL, color=GREY)
ax.set_ylabel("Transformation capacity  (complexity + governance, z)",
              fontsize=FS_LABEL, color=GREY)
ax.tick_params(colors=GREY, labelsize=FS_TICK, length=3)
for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_color(GREY)
    spine.set_linewidth(0.8)

fig.tight_layout()
fig.savefig(OUTF / "typology_2x2.png", dpi=600, facecolor="white")
fig.savefig(OUTF / "typology_2x2.svg", facecolor="white")
print(f"\nSaved -> {OUTF/'typology_2x2.png'}, {OUTF/'typology_2x2.svg'}")