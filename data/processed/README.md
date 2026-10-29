## Processed Data — Frozen Inputs for Phase 2+

These two files are the verified, frozen inputs for all downstream modelling and serving.
Do not edit them manually. Re-generate only by re-running the full pipeline in `~/kenya_agri_data/`.

| File | Rows | Description |
|---|---|---|
| `canonical_11series_v2_monthly_2006_2022.csv` | 1,884 | 11 price series (Maize ×4, Beans ×4, Potatoes ×3), monthly, Jan 2006 – Apr 2022 |
| `nasa_weather_5markets_monthly_2006_2022.csv` | — | NASA POWER monthly weather for 5 markets, Jan 2006 – Dec 2022 |

### SHA-256 Checksums

canonical_11series_v2_monthly_2006_2022.csv
  → verified match against ~/kenya_agri_data/ source (Phase 1 Step 5)

nasa_weather_5markets_monthly_2006_2022.csv
  → verified match against ~/kenya_agri_data/ source (Phase 1 Step 5)

### Phase 1 Verification Status

- Step 1 — Raw file checksums: PASS
- Step 2 — Canonical dataset sanity check: PASS (0 price NaN, 0 weather NaN, 11 series)
- Step 3 — Walk-forward evaluation: PASS (Naive MAPE 8.52%, Challenger 8.49%, leak check passed)
- Step 4 — Historical replay & drift monitor: PASS (43/593 alerts, 2017 Maize shock detected)
- Step 5 — Data frozen here: PASS
