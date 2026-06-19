import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
YEAR = 2021

SA_COUNTRIES = {
    "Argentina":"ARG","Bolivia":"BOL","Brazil":"BRA","Brasil":"BRA","Chile":"CHL",
    "Colombia":"COL","Ecuador":"ECU","Guyana":"GUY","Paraguay":"PRY",
    "Peru":"PER","Perú":"PER","Suriname":"SUR","Surinam":"SUR",
    "Uruguay":"URY","Venezuela":"VEN",
}

# Primary fossil sources
FOSSIL_PRIMARY = ["PETRÓLEO", "GAS NATURAL", "CARBÓN MINERAL"]

# Secondary fossil-derived carriers (imputed only as NET IMPORTS to avoid
# double-counting the crude that refiners already report as primary)
FOSSIL_DERIVED = [
    "GAS LICUADO DE PETRÓLEO","GASOLINA SIN ETANOL","GASOLINA CON ETANOL",
    "KEROSENE/JET FUEL","DIÉSEL OIL SIN BIODIÉSEL","DIÉSEL OIL CON BIODIÉSEL",
    "FUEL OIL","COQUE","GASES",
]

# All primary sources (denominator base)
PRIMARY_ALL = [
    "PETRÓLEO","GAS NATURAL","CARBÓN MINERAL","NUCLEAR","HIDROENERGÍA",
    "GEOTERMIA","EÓLICA","SOLAR","LEÑA","BAGAZO DE CAÑA","ETANOL",
    "BIODIÉSEL","BIOGÁS","OTRA BIOMASA","OTRAS PRIMARIAS",
]

def _norm(s: str) -> str:
    return str(s).strip().upper()

def _row(raw, cols, label):
    """Return a numeric Series for a given row label, indexed by source names."""
    first_col = raw.iloc[:, 0].apply(_norm)
    mask = first_col.eq(_norm(label))
    if not mask.any():
        return None
    row = raw[mask].iloc[0]
    row.index = cols
    return pd.to_numeric(row, errors="coerce")

def load_f1_fossil(filename: str, year: int = YEAR) -> pd.DataFrame:
    xls = pd.ExcelFile(RAW / filename)
    recs = {}
    for sheet in xls.sheet_names:
        if not sheet.strip().startswith(str(year)):
            continue
        country_raw = sheet.split("-")[-1].strip()
        iso3 = SA_COUNTRIES.get(country_raw)
        if iso3 is None:
            print(f"  [skip] '{sheet}'")
            continue

        raw = pd.read_excel(xls, sheet_name=sheet, header=None)
        header_row = raw.apply(
            lambda r: r.astype(str).str.contains("PETRÓLEO", case=False, na=False).any(),
            axis=1
        ).idxmax()
        cols = [_norm(c) for c in raw.iloc[header_row].tolist()]

        oferta = _row(raw, cols, "OFERTA TOTAL")
        imp    = _row(raw, cols, "IMPORTACIÓN")
        exp    = _row(raw, cols, "EXPORTACIÓN")
        if oferta is None:
            print(f"  [warn] no OFERTA TOTAL in '{sheet}'")
            continue

        def grab(series, names):
            if series is None:
                return 0.0
            present = [_norm(n) for n in names if _norm(n) in series.index]
            return series[present].fillna(0).sum()

        # Part 1: primary fossils in total supply
        fossil_primary = grab(oferta, FOSSIL_PRIMARY)

        # Part 2: NET imported fossil derivatives (import - export), floored at 0
        deriv_imp = grab(imp, FOSSIL_DERIVED)
        deriv_exp = grab(exp, FOSSIL_DERIVED)
        deriv_net_import = max(deriv_imp - deriv_exp, 0.0)

        fossil_total = fossil_primary + deriv_net_import

        # Denominator: total primary supply + net imported fossil derivatives
        total_primary = grab(oferta, PRIMARY_ALL)
        denom = total_primary + deriv_net_import

        share = (fossil_total / denom) * 100 if denom else None
        recs[iso3] = {
            "f1_fossil": share,
            "fossil_primary": fossil_primary,
            "deriv_net_import": deriv_net_import,
            "denom": denom,
        }
        print(f"  {iso3}: primary_fossil={fossil_primary:,.0f}  "
              f"net_deriv_imp={deriv_net_import:,.0f}  share={share:,.1f}%")

    df = pd.DataFrame(recs).T
    return df

if __name__ == "__main__":
    df = load_f1_fossil("Matriz_balance_energetico.xlsx")
    print("\n", df["f1_fossil"].sort_values(ascending=False))