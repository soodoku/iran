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

## Raw data

The `data/` folder contains the bundled source files used in the build:

- `HDR25_Composite_indices_complete_time_series.csv` — UNDP HDR 2025 composite time series
- `WB_WDI_SP_DYN_LE00_IN_WIDEF.csv` — World Bank life expectancy
- `WB_WDI_SH_DYN_MORT_WIDEF.csv` — World Bank under-5 mortality
- `WB_GS_WIDEF.csv` — World Bank Gender Statistics (used here for tertiary enrollment)
- `WB_HNP_WIDEF.csv` — World Bank Health Nutrition and Population data (used here for maternal mortality)

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
