import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
xls = pd.ExcelFile(RAW / "Matriz_balance_energetico.xlsx")

for sheet in xls.sheet_names:
    if sheet.strip().startswith("2021") and any(c in sheet for c in ["Chile", "Argentina", "Guyana"]):
        print(f"\n===== {sheet} =====")
        raw = pd.read_excel(xls, sheet_name=sheet, header=None)
        header_row = raw.apply(lambda r: r.astype(str).str.contains("PETRÓLEO", na=False).any(), axis=1).idxmax()
        cols = [str(c).strip() for c in raw.iloc[header_row].tolist()]
        first_col = raw.iloc[:, 0].apply(lambda x: str(x).strip().upper())
        oferta = raw[first_col.eq("OFERTA TOTAL")].iloc[0]
        oferta.index = cols
        vals = pd.to_numeric(oferta, errors="coerce")
        # imprime solo columnas con valor
        for name, v in vals.items():
            if pd.notna(v) and v != 0:
                print(f"  {name:35s} {v:,.0f}")
