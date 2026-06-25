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

## F5 Governance — World Bank WGI
- Indicators: GE.EST, RL.EST, RQ.EST (government effectiveness, rule of law, regulatory quality)
- Aggregation: simple mean of the three estimates
- Year used: 2022
