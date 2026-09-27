# Data sources — cell-level provenance

## F1 Fossil share — OLADE/SIELAC, 2021, unit: 10³ bep
- Definition: fossil share of total energy supply
- Numerator: primary fossils (oil+gas+coal) in OFERTA TOTAL
  + NET imported fossil derivatives (import − export, floored at 0)
- Denominator: TOTAL PRIMARIAS + net imported fossil derivatives
- Rationale: net-import imputation captures fossil consumption of
  non-refining countries (e.g. Guyana imports refined products) while
  avoiding double-counting crude that refiners report as both primary
  and secondary.
- Reference countries (NOR/AUS/CAN/KOR/QAT): not in OLADE → NaN (not used in typology)

## F2 ECI — Harvard Atlas of Economic Complexity
- URL: https://atlas.cid.harvard.edu/  (Rankings → download)
- Year used: 2022
- Notes: Guyana/Suriname may be missing → document fallback or exclusion

## F3 Natural resource rents — World Bank WDI
- Indicator code: NY.GDP.TOTL.RT.ZS
- Year used: 2021 (or nearest)

## CO2e intensity of energy consumption (2000 vs 2024 figure) — OLADE/SIELAC
- File: data/raw/Energy_intensity.xlsx (Indicadores: Ambientales →
  "Índice de emisiones por energía consumida", unit: t / tep, 2000-2024, 12 countries)
- One sheet per pollutant: CO2, NO2, hydrocarbons, CH4, CO, particulates.
  SIELAC offers no CO2e series, so CO2e is built here.
- Conversion (notebooks/09_fig_co2_intensity.py):
  CO2e [t/tep] = CO2 + 28 × CH4 (IPCC AR5 GWP100); g/MJ = t/tep × 10^6 / 41,868
  (1 tep = 10^7 kcal = 41.868 GJ, OLADE convention).
- NOT included: N2O (not downloaded). "DIÓXIDO DE NITRÓGENO" is NO2, not N2O, and
  has no GWP; CO, hydrocarbons and particulates are not GHGs and are excluded.
  CH4 adds ≤0.4% to CO2 in 2024 (Brazil highest), so CO2e ≈ CO2 here.
- Comparison year: 2024, the latest year of the OLADE release (the locked reference
  year of the typology fronts stays 2022; this figure is a temporal comparison, not a
  front). Manuscript text that quotes this figure must be updated accordingly.
- % change = (2024 − 2000) / 2024 × 100, i.e. relative to the comparison year, as in
  the original R figure; kept in outputs/tables/co2_intensity_2000_2024.csv with sign
  (+ = intensity rose). Not drawn: bar length carries the magnitude.
- Cross-check (independent): OLADE intensity vs Global Carbon Project CO2 (OWID
  owid-co2-data.csv) ÷ OLADE final consumption (current per-country balances).
  Agreement within ±10% for 11/12 countries in 2000, 10/12 in 2022 and 9/12 within
  ±14% in 2024. Persistent gaps: Suriname (OLADE 28-36% below the external estimate in
  2022-24), Guyana (14-28% below) and Bolivia 2024 (21% below); small energy systems,
  not corrected. Colombia 2000 was the only clear outlier (ratio 1.83), see below.
- Series checks (all 12 countries, 2000-2024): range 20-155 g/MJ, no gaps or non-positive
  values. 2000 within ±13% of the 2001-03 median for every country; 2024 within ±11% of
  the 2021-23 median except Uruguay (−21%) and Chile (−11%). Year-over-year jumps >15%
  never fall on 2000 or 2024 (largest: Venezuela 2014-17, up to 155 g/MJ, economic
  collapse; isolated spikes Colombia and Peru 2009). Uruguay's −62% is a real trend
  (38.9 → 37.5 → 33.6 → 29.7 in 2021-24) but sensitive to the endpoints: 2000 is 13%
  above its neighbours; both endpoints match the external estimate (49.9 / 30.6).
  Colombia's OLADE series is inflated for the whole 2000-2011 period, not only 2000;
  any other use of it needs the same care. Limit: the external check uses OLADE final
  consumption as denominator, so it validates the emissions numerator, not consumption.
- CORRECTION applied — Colombia 2000: OLADE indicator gives 111 g/MJ, which implies
  0.51 EJ of energy consumed; both OLADE's own CO2 (56.96 Mt, ≈ GCP 56.2 Mt) and any
  plausible consumption (0.93 EJ) give ~61 g/MJ. The 2000 final consumption in the OLADE
  historical balance is itself an outlier (+27% vs mean 2001-02; final/primary energy
  1.04 vs 0.72-0.85 in other years), so the mean of 2001-02 is used. Corrected value
  61.4 g/MJ (external check: 60.6). Inputs and method in
  data/processed/co2_intensity_corrections.csv; the raw OLADE value is kept in
  outputs/tables/co2_intensity_2000_2024.csv (column olade_indicator_co2e_g_mj_2000,
  flag `corrected`). Effect: Colombia changes from a large decline (111 → 69) to a
  moderate rise (61 → 69). To be confirmed with OLADE; every other country uses the
  indicator as published.
- Interpretation caveat: the metric divides whole-energy-sector emissions (extraction,
  refining, flaring, power) by domestic FINAL consumption. Hydrocarbon exporters look
  high: Venezuela's final consumption is 25% of its production (49% exported, 32% own
  use/losses/flared), Guyana's 6%. With CO2 per unit of primary energy (2022) Venezuela
  is mid-range (47 g/MJ) and Guyana highest (86). Suggested caption note: "Intensity
  is per unit of final energy consumption; hydrocarbon exporters (Venezuela, Guyana,
  Suriname) appear high because emissions from producing exported energy are
  attributed to domestic consumption."
- Supersedes the R figure (Matriz energética.R, l. 805-834): it used an older OLADE
  download (e.g. Venezuela 2022 final consumption 253,738 vs 143,184 in the current
  release; Paraguay −10%, Chile +13%).

## F5 Governance — World Bank WGI
- Indicators: GE.EST, RL.EST, RQ.EST (government effectiveness, rule of law, regulatory quality)
- Aggregation: simple mean of the three estimates
- Year used: 2022

## Critical minerals: SA share of world production and reserves (notebooks/11_fig_minerals.py)
- File: data/processed/minerals_usgs_mcs2024.csv (committed — hand-transcribed from the
  public PDFs below, not a private download, so it doesn't follow the data/raw pattern).
- Replaces the R version (manipulaciondata.R, l. 155-178), which read a
  `Minerals.xlsx` that only existed on the old machine (Downloads folder) and was never
  copied anywhere durable — not recoverable, so this rebuilds the table from the original
  public source instead.
- Source: USGS Mineral Commodity Summaries 2024 (data as of Jan. 2024, mine production
  is the 2023 estimate), one PDF per commodity:
  https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-{copper,graphite,lithium,nickel,
  rare-earths,silver}.pdf — each has a "World Mine Production and Reserves" table.
  Silver's world reserves total carries a March 5, 2024 USGS correction (610,000 t,
  marked with * in the source table); used here since it's the standing figure.
- Method (matches the R script exactly — cross-checked, see below): per mineral,
  each SA country's bar segment = its 2023e mine production / world 2023e mine
  production; the black dot = the summed reserves of the SA countries with any
  production, as a share of world reserves. Countries with no reported production
  contribute 0 (most minerals: only 1-4 of the 5 countries produce it at all).
- Values used (mine production 2023e; reserves) — Argentina, Bolivia, Brazil, Chile,
  Peru; "—" = not in the source table, treated as 0:
  - Copper (thousand t Cu): Chile 5,000; 190,000 · Peru 2,600; 120,000 · World 22,000; 1,000,000
  - Graphite (t): Brazil 73,000; 74,000,000 · World 1,600,000; 280,000,000
  - Lithium (t Li): Argentina 9,600; 3,600,000 · Brazil 4,900; 390,000 ·
    Chile 44,000; 9,300,000 · World 180,000; 28,000,000
  - Nickel (t Ni): Brazil 89,000; 16,000,000 · World 3,600,000; 130,000,000
  - Rare earths (t REO eq.): Brazil 80; 21,000,000 · World 350,000; 110,000,000
  - Silver (t Ag): Argentina 910; 6,500 · Bolivia 1,200; 22,000 · Chile 1,400; 26,000 ·
    Peru 3,100; 110,000 · World 26,000; 610,000
- Cross-check against the old reference figure (screenshot of the R output, no
  underlying data file): recomputed bar totals and dot values from the table above
  reproduce the reference chart almost exactly — e.g. Copper bar 34.5% (image ~34.5%),
  dot 31.0% (~31%); Lithium bar 32.5% (~32.5%), dot 47.5% (~47%); Nickel bar 2.5%
  (~2.5%), dot 12.3% (~12%); Rare earths bar ~0.02% (negligible, as in the image), dot
  19.1% (~19%); Graphite bar 4.6% (~4.5%), dot 26.4% (~26.5%); Silver bar 25.4%
  (~26%), dot 27.0% (image read ~23%, the one visible gap — likely just imprecision
  reading a dot position off a static screenshot, or the pre-March-2024-correction
  silver reserves total; not re-derivable without the original file).
