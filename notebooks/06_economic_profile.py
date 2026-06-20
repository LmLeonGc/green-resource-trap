import wbgapi as wb
import pandas as pd
import numpy as np
from pathlib import Path

PROC = Path("data/processed"); OUTT = Path("outputs/tables")
ISO3_SA = ["ARG","BOL","BRA","CHL","COL","ECU","GUY","PRY","PER","SUR","URY","VEN"]

# --- Indicators to characterise economic (in)stability and development ---
IND = {
    "NY.GDP.PCAP.KD":      "gdp_pc",          # GDP per capita (constant)
    "NY.GDP.MKTP.KD.ZG":   "gdp_growth",      # GDP growth (annual %)
    "NY.GDP.TOTL.RT.ZS":   "res_rents",       # resource rents % GDP (context)
    "SI.POV.GINI":         "gini",            # inequality
    "FP.CPI.TOTL.ZG":      "inflation",       # inflation (instability proxy)
    "SL.UEM.TOTL.ZS":      "unemployment",    # unemployment
}

# Pull a TIME SERIES 2010-2021 so we can compute volatility, not just levels
YEARS = range(2010, 2022)

frames = {}
for code, name in IND.items():
    try:
        df = wb.data.DataFrame(code, ISO3_SA, time=YEARS, labels=False)
        frames[name] = df
        print(f"  OK  {name:14s} shape={df.shape}")
    except Exception as e:
        print(f"  FAIL {name:14s} {e}")

# ---- Build country-level features ----
feat = pd.DataFrame(index=ISO3_SA)

# Level (most recent ~2021) and volatility (std over the decade)
def level_and_vol(name, year_col_hint="YR2021"):
    df = frames[name]
    # latest available per country
    latest = df.apply(lambda r: r.dropna().iloc[-1] if r.dropna().size else np.nan, axis=1)
    vol = df.std(axis=1, ddof=0)
    return latest, vol

if "gdp_pc" in frames:
    feat["gdp_pc_2021"], _ = level_and_vol("gdp_pc")
if "gdp_growth" in frames:
    g_mean = frames["gdp_growth"].mean(axis=1)
    g_vol  = frames["gdp_growth"].std(axis=1, ddof=0)
    feat["gdp_growth_mean"] = g_mean
    feat["gdp_growth_volatility"] = g_vol      # <-- KEY variable for the thesis
if "inflation" in frames:
    feat["inflation_volatility"] = frames["inflation"].std(axis=1, ddof=0)
    feat["inflation_mean"] = frames["inflation"].mean(axis=1)
if "gini" in frames:
    feat["gini"], _ = level_and_vol("gini")
if "unemployment" in frames:
    feat["unemployment_mean"] = frames["unemployment"].mean(axis=1)

# ---- Join with typology ----
typ = pd.read_csv(OUTT / "typology.csv", index_col="iso3")
out = typ[["country","type"]].join(feat)
print("\n", out.round(2).to_string())

print("\n--- Means by typology group ---")
print(out.groupby("type").mean(numeric_only=True).round(2).to_string())

out.to_csv(OUTT / "economic_profile.csv")