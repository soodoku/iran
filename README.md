# Iran comparative package (full rebuild)

This package fixes four concrete issues:

1. **Iran is not included in its own peer group.**
2. **The included script rebuilds all eight PNGs from the bundled raw data.**
3. **The main line charts show all 14 peer countries rather than a privileged Brazil-versus-Iran comparison.**
4. **Iran and the peer median now use high-contrast colors**: Iran is blue and the peer median is orange.

## Peer definition

The benchmark cohort is defined as:

- anchor country: **Iran (IRN)**
- anchor year: **1990**
- rule: countries with 1990 HDI within **±0.020** of Iran's 1990 HDI
- **Iran itself is excluded** from the peer group
- aggregates such as World/regions are excluded

That yields 14 peers.

## Data sources

The `data/` folder contains the following datasets:

| File | Source | Indicator(s) | URL |
|------|--------|--------------|-----|
| `HDR25_Composite_indices_complete_time_series.csv` | UNDP Human Development Report 2025 | HDI, life expectancy, mean/expected years of schooling, GNI per capita (1990–2023) | https://hdr.undp.org/data-center/documentation-and-downloads |
| `WB_WDI_SP_DYN_LE00_IN_WIDEF.csv` | World Bank WDI | Life expectancy at birth (SP.DYN.LE00.IN) | https://data.worldbank.org/indicator/SP.DYN.LE00.IN |
| `WB_WDI_SH_DYN_MORT_WIDEF.csv` | World Bank WDI | Under-5 mortality rate (SH.DYN.MORT) | https://data.worldbank.org/indicator/SH.DYN.MORT |
| `WB_GS_WIDEF.csv` | World Bank Gender Statistics | Tertiary enrollment, gross (SE.TER.ENRR) | https://data.worldbank.org/indicator/SE.TER.ENRR |
| `WB_HNP_WIDEF.csv` | World Bank HNP | Maternal mortality ratio (SH.STA.MMRT) | https://data.worldbank.org/indicator/SH.STA.MMRT |

## Rebuild

From the package root:

```bash
python scripts/build_figures.py
```

What the script does:

- deletes any stale PNGs from `figs/`
- rebuilds **all eight** figure PNGs in `figs/`
- stops with an error if any expected PNG is missing after the rebuild

## Figure list

1. `01_hdi_trajectory.png` — Iran plus all 14 peers, with peer median
2. `02_life_expectancy.png` — Iran plus all 14 peers, with peer median
3. `03_under5_mortality.png` — Iran plus all 14 peers, with peer median; restricted to 2000–2023 and scaled to the cohort 90th percentile so central variation is visible
4. `04_mean_years_schooling.png`
5. `05_expected_years_schooling.png`
6. `06_tertiary_enrollment.png`
7. `07_maternal_mortality.png`
8. `08_hdi_gain_rank.png` — peer-country bars plus Iran as a reference line

## Notes

- The maternal mortality series in the bundled HNP file runs through 2020.
- The Iranian tertiary enrollment series in the bundled GS file runs through 2020.
- Under-5 mortality is shown from **2000 onward**, and the y-axis is capped to foreground the central peer variation rather than two early outlier series.
