import requests
import pandas as pd
import wbgapi as wb
from pathlib import Path

import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("olade", Path(__file__).parent / "02_load_olade.py")
olade = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(olade)

# --- South American sample ---
ISO3_SA = ["ARG","BOL","BRA","CHL","COL","ECU","GUY","PRY","PER","SUR","URY","VEN"]
# --- Global reference anchors (NOT part of the typology; scale anchors only) ---
ISO3_REF = ["NOR","AUS","CAN","KOR","QAT"]
ISO3 = ISO3_SA + ISO3_REF

COUNTRY_NAMES = {
    "ARG":"Argentina","BOL":"Bolivia","BRA":"Brazil","CHL":"Chile",
    "COL":"Colombia","ECU":"Ecuador","GUY":"Guyana","PRY":"Paraguay",
    "PER":"Peru","SUR":"Suriname","URY":"Uruguay","VEN":"Venezuela",
    "NOR":"Norway","AUS":"Australia","CAN":"Canada","KOR":"South Korea","QAT":"Qatar",
}

YEAR = 2021
ATLAS_URL = "https://atlas.hks.harvard.edu/api/graphql"

# Documented proxies for missing values (year used noted for sources.md / flag)
F3_PROXY = {
    "VEN": (11.846508, 2014),  # WB ceased reporting after 2014; structural dependence underestimated
}

OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

# ---------- F2: Atlas ECI ----------
def _atlas_query(query: str) -> dict:
    r = requests.post(ATLAS_URL, json={"query": query}, timeout=60)
    r.raise_for_status()
    payload = r.json()
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]

def _to_int_id(cid):
    return cid if isinstance(cid, int) else int(str(cid).split("-")[-1])

def load_f2_eci(year: int = YEAR) -> pd.Series:
    countries = _atlas_query("{ locationCountry { countryId iso3Code } }")["locationCountry"]
    id_by_iso3 = {c["iso3Code"]: _to_int_id(c["countryId"]) for c in countries}
    rec = {}
    for iso3 in ISO3:
        cid = id_by_iso3.get(iso3)
        if cid is None:
            rec[iso3] = None
            continue
        data = _atlas_query(
            f"{{ countryYear(countryId: {cid}, yearMin: {year}, yearMax: {year}) {{ year eci }} }}"
        )["countryYear"]
        rec[iso3] = data[0]["eci"] if (data and data[0]["eci"] is not None) else None
    return pd.Series(rec, name="f2_eci")

# ---------- F3: World Bank natural resource rents ----------
def load_f3_rents(year: int = YEAR):
    df = wb.data.DataFrame("NY.GDP.TOTL.RT.ZS", ISO3, time=year)
    s = df.iloc[:, 0]
    s.name = "f3_rents"
    flag = pd.Series(False, index=s.index, name="f3_rents_imputed")
    # Apply documented proxies where the reference year is missing
    for iso3, (val, yr) in F3_PROXY.items():
        if iso3 in s.index and pd.isna(s.get(iso3)):
            s.loc[iso3] = val
            flag.loc[iso3] = True
    return s, flag

# ---------- F5: World Bank governance (mean of GE, RL, RQ), db=3 ----------
def load_f5_governance(year: int = YEAR) -> pd.Series:
    inds = ["GOV_WGI_GE.EST", "GOV_WGI_RL.EST", "GOV_WGI_RQ.EST"]
    df = wb.data.DataFrame(inds, ISO3, time=year, db=3)
    s = df.mean(axis=1)
    s.name = "f5_gov"
    return s

# ---------- Assemble ----------
def assemble():
    master = pd.DataFrame(index=ISO3)
    master.index.name = "iso3"
    master["country"] = master.index.map(COUNTRY_NAMES)
    master["group"]   = ["South America" if c in ISO3_SA else "reference" for c in master.index]

    # F1 — OLADE fossil share (only South America; reference countries -> NaN)
    f1_df = olade.load_f1_fossil("Matriz_balance_energetico.xlsx")
    master["f1_fossil"] = f1_df["f1_fossil"]

    master["f2_eci"]   = load_f2_eci()
    f3, f3_flag        = load_f3_rents()
    master["f3_rents"] = f3
    master["f3_rents_imputed"] = f3_flag
    master["f5_gov"]   = load_f5_governance()

    master.to_csv(OUT / "master_table.csv")
    print(master.round(3).to_string())
    print("\nMissing values per front (South America only):")
    sa = master[master["group"] == "South America"]
    print(sa[["f1_fossil","f2_eci","f3_rents","f5_gov"]].isna().sum())
    return master

if __name__ == "__main__":
    assemble()