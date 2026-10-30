from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    commodities = ["Maize", "Beans (dry)", "Potatoes (Irish)"]
    markets = ["Nairobi", "Eldoret"]

    years = range(2006, 2020)
    records = []
    weather_records = []

    np.random.seed(42)

    for c in commodities:
        for mkt in markets:
            base_price = 30.0 if c == "Maize" else (50.0 if c == "Beans (dry)" else 25.0)
            for y in years:
                for m in range(1, 13):
                    ym = f"{y}-{m:02d}"
                    if y == 2015 and m in (4, 5):
                        continue

                    price = base_price + np.random.uniform(-5.0, 5.0) + (y - 2006) * 1.5
                    records.append({
                        "canonical_commodity": c,
                        "market": mkt,
                        "year_month": ym,
                        "price_per_kg_kes": round(price, 2),
                    })

    for mkt in markets:
        for y in years:
            for m in range(1, 13):
                ym = f"{y}-{m:02d}"
                weather_records.append({
                    "market": mkt,
                    "year_month": ym,
                    "temp_mean_c": round(20.0 + np.random.uniform(-3, 3), 1),
                    "precip_total_mm": round(50.0 + np.random.uniform(-20, 40), 1),
                    "humidity_mean_pct": round(60.0 + np.random.uniform(-10, 10), 1),
                    "rainy_days_count": int(np.random.randint(1, 15)),
                })

    prices_df = pd.DataFrame(records)
    weather_df = pd.DataFrame(weather_records)
    return prices_df, weather_df
