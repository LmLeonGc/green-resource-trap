import pandas as pd
import numpy as np
from pathlib import Path

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

COUNTRIES = {
    "ARG": "Argentina", "BOL": "Bolivia", "BRA": "Brazil", "CHL": "Chile",
    "COL": "Colombia", "ECU": "Ecuador", "GUY": "Guyana", "PRY": "Paraguay",
    "PER": "Peru", "SUR": "Suriname", "URY": "Uruguay", "VEN": "Venezuela",
}

# Each loader returns a Series indexed by ISO3.
# Fill these in as you download. Keep raw files untouched in data/raw/.

def load_f1_fossil():
    # OLADE/SIELAC: build fossil share = (oil+gas+coal)/total primary supply, 2022
    df = pd.read_csv(RAW / "olade_primary_2022.csv")
    # ... reshape to ISO3 → fossil_share_pct
    raise NotImplementedError("plug in OLADE parsing")

def load_f2_eci():
    df = pd.read_csv(RAW / "harvard_eci_2022.csv")
    # ... ISO3 → eci
    raise NotImplementedError

def load_f3_rents():
    # World Bank WDI NY.GDP.TOTL.RT.ZS
    df = pd.read_csv(RAW / "wb_resource_rents.csv", skiprows=4)
    raise NotImplementedError

def load_f5_governance():
    # WGI: mean of GE.EST, RL.EST, RQ.EST
    raise NotImplementedError

def assemble():
    master = pd.DataFrame(index=list(COUNTRIES.keys()))
    master["country"] = master.index.map(COUNTRIES)
    # master["f1_fossil"] = load_f1_fossil()
    # master["f2_eci"]    = load_f2_eci()
    # master["f3_rents"]  = load_f3_rents()
    # master["f5_gov"]    = load_f5_governance()
    master.to_csv(OUT / "master_table.csv")
    print(master)
    return master

if __name__ == "__main__":
    assemble()