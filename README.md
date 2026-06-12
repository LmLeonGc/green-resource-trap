# Green Resource Trap — South America Energy Transition

Reproducible analysis behind the typology and correlation results in
"A Continent in Transition: South America's Emerging Leadership in Global Clean Energy"
(EREN-100378, Environmental Research: Energy).

## Frentes (analytical fronts)
| Code | Front | Variable | Source | Ref year |
|------|-------|----------|--------|----------|
| F1 | Energy structure | Fossil share of primary energy (%) | OLADE/SIELAC | 2022 |
| F2 | Transformation capacity | Economic Complexity Index (ECI) | Harvard Atlas | 2022 |
| F2b| Robustness | Global Innovation Index | WIPO GII | 2022 |
| F3 | Extractive exposure | Natural resource rents (% GDP) | World Bank WDI | 2022 |
| F4 | Territorial pressure | Mineral endowment × forest/water pressure | USGS + GFW | 2022 (tentative) |
| F5 | Institutional capacity | Worldwide Governance Indicators (avg) | World Bank WGI | 2022 |

## Countries (n=12)
ARG, BOL, BRA, CHL, COL, ECU, GUY, PRY, PER, SUR, URY, VEN

## Methodological decisions (locked)
- Reference year: 2022 (nearest-available fallback documented per cell in data/sources.md)
- Normalisation: z-score across the 12 countries, per front
- Typology: explicit theoretical thresholds (primary) + hierarchical clustering (robustness)
- Correlations: Spearman rho, reported with 95% CI; associative not causal (n=12)
- F4 included as a clustering axis ONLY if data quality permits; otherwise interpretive
