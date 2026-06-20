import pandas as pd
import numpy as np
from scipy.stats import spearmanr, kruskal
from pathlib import Path

OUTT = Path("outputs/tables")

econ = pd.read_csv(OUTT / "economic_profile.csv", index_col="iso3")
val  = pd.read_csv(OUTT / "validation.csv", index_col="iso3")   # has delta_fossil

df = econ.join(val[["delta_fossil"]])

# ---------- 1. Volatility by group, WITH and WITHOUT Venezuela ----------
print("=== Growth volatility by type — WITH Venezuela ===")
print(df.groupby("type")["gdp_growth_volatility"].agg(["median","mean","count"]).round(2).to_string())

print("\n=== Growth volatility by type — WITHOUT Venezuela ===")
dfx = df.drop("VEN")
print(dfx.groupby("type")["gdp_growth_volatility"].agg(["median","mean","count"]).round(2).to_string())

# Kruskal across groups (without VEN), trap vs the rest
print("\n=== Trap vs non-trap (without VEN): growth volatility ===")
trap = dfx[dfx["type"]=="Green resource trap"]["gdp_growth_volatility"].dropna()
rest = dfx[dfx["type"]!="Green resource trap"]["gdp_growth_volatility"].dropna()
print(f"  trap   median={trap.median():.2f}  mean={trap.mean():.2f}  n={len(trap)}")
print(f"  rest   median={rest.median():.2f}  mean={rest.mean():.2f}  n={len(rest)}")
H,p = kruskal(trap, rest)
print(f"  Kruskal-Wallis: H={H:.2f}, p={p:.3f}")

# ---------- 2. Does volatility explain ERRATIC energy trajectory? ----------
# Hypothesis: higher economic volatility -> larger absolute swing in fossil share
df["abs_delta_fossil"] = df["delta_fossil"].abs()

print("\n=== Economic volatility vs magnitude of energy-matrix swing ===")
for label, d in [("ALL 12", df), ("WITHOUT VEN", df.drop("VEN")),
                 ("WITHOUT VEN+GUY", df.drop(["VEN","GUY"]))]:
    dd = d[["gdp_growth_volatility","abs_delta_fossil"]].dropna()
    rho,p = spearmanr(dd["gdp_growth_volatility"], dd["abs_delta_fossil"])
    print(f"  {label:16s}  rho={rho:+.3f}  p={p:.3f}  n={len(dd)}")

# ---------- 3. Quick table: the story per country ----------
print("\n=== Country story (sorted by growth volatility) ===")
show = df[["country","type","gdp_growth_volatility","gdp_growth_mean",
           "delta_fossil","gdp_pc_2021"]].round(2)
print(show.sort_values("gdp_growth_volatility", ascending=False).to_string())