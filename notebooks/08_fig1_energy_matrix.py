import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

RAW = Path("data/raw")
OUTF = Path("outputs/figures"); OUTF.mkdir(parents=True, exist_ok=True)

FOSSIL_PRIMARY = ["PETRÓLEO", "GAS NATURAL", "CARBÓN MINERAL"]
FOSSIL_DERIVED = [
    "GAS LICUADO DE PETRÓLEO","GASOLINA SIN ETANOL","GASOLINA CON ETANOL",
    "KEROSENE/JET FUEL","DIÉSEL OIL SIN BIODIÉSEL","DIÉSEL OIL CON BIODIÉSEL",
    "FUEL OIL","COQUE","GASES",
]
PRIMARY_ALL = [
    "PETRÓLEO","GAS NATURAL","CARBÓN MINERAL","NUCLEAR","HIDROENERGÍA",
    "GEOTERMIA","EÓLICA","SOLAR","LEÑA","BAGAZO DE CAÑA","ETANOL",
    "BIODIÉSEL","BIOGÁS","OTRA BIOMASA","OTRAS PRIMARIAS",
]
# For the stacked composition we group sources into readable categories
GROUPS = {
    "Oil":       ["PETRÓLEO"],
    "Gas":       ["GAS NATURAL"],
    "Coal":      ["CARBÓN MINERAL"],
    "Hydro":     ["HIDROENERGÍA"],
    "Nuclear":   ["NUCLEAR"],
    "Other renewables": ["GEOTERMIA","EÓLICA","SOLAR"],
    "Biomass":   ["LEÑA","BAGAZO DE CAÑA","ETANOL","BIODIÉSEL","BIOGÁS","OTRA BIOMASA"],
    "Other":     ["OTRAS PRIMARIAS"],
}

def _norm(s): return str(s).strip().upper()

def _row(raw, cols, label):
    fc = raw.iloc[:,0].apply(_norm)
    m = fc.eq(_norm(label))
    if not m.any(): return None
    r = raw[m].iloc[0]; r.index = cols
    return pd.to_numeric(r, errors="coerce")

def load_series(filename):
    xls = pd.ExcelFile(RAW / filename)
    records = {}
    for sheet in xls.sheet_names:
        s = sheet.strip()
        # sheets look like "1990 - América del Sur"
        if "del sur" not in s.lower():
            continue
        try:
            year = int(s.split("-")[0].strip())
        except ValueError:
            continue
        raw = pd.read_excel(xls, sheet_name=sheet, header=None)
        hdr = raw.apply(lambda r: r.astype(str).str.contains("PETRÓLEO", na=False).any(), axis=1).idxmax()
        cols = [_norm(c) for c in raw.iloc[hdr].tolist()]
        oferta = _row(raw, cols, "OFERTA TOTAL")
        imp    = _row(raw, cols, "IMPORTACIÓN")
        exp    = _row(raw, cols, "EXPORTACIÓN")
        if oferta is None: continue

        def grab(series, names):
            if series is None: return 0.0
            present = [_norm(n) for n in names if _norm(n) in series.index]
            return series[present].fillna(0).sum()

        deriv_net = max(grab(imp, FOSSIL_DERIVED) - grab(exp, FOSSIL_DERIVED), 0.0)
        # composition by group (primary supply)
        comp = {g: grab(oferta, names) for g, names in GROUPS.items()}
        # add net-imported fossil derivatives into the fossil side (Oil proxy)
        comp["Oil"] += deriv_net
        total = sum(comp.values())
        fossil = comp["Oil"] + comp["Gas"] + comp["Coal"]
        records[year] = {**comp, "TOTAL": total, "fossil_share": fossil/total*100}
    df = pd.DataFrame(records).T.sort_index()
    return df

if __name__ == "__main__":
    df = load_series("Matriz_balance_energetico_serie.xlsx")  # adjust filename
    print(df[["TOTAL","fossil_share"]].round(1).to_string())
    print(f"\nFossil share 1990: {df['fossil_share'].iloc[0]:.1f}%")
    print(f"Fossil share latest ({df.index[-1]}): {df['fossil_share'].iloc[-1]:.1f}%")

    # Stacked area figure
    group_cols = list(GROUPS.keys())
    fig, ax = plt.subplots(figsize=(10,6))
    ax.stackplot(df.index, *[df[g] for g in group_cols], labels=group_cols)
    ax.set_xlabel("Year")
    ax.set_ylabel("Primary energy supply (10³ bep)")
    ax.set_title("South America: primary energy supply by source, 1990–2024")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    ax.set_xlim(df.index.min(), df.index.max())
    fig.tight_layout()
    fig.savefig(OUTF / "fig1_energy_matrix.png", dpi=200)
    print(f"\nSaved -> {OUTF/'fig1_energy_matrix.png'}")