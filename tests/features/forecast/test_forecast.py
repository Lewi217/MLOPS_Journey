from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.features.forecast.features import build_all, leak_check, to_m
from app.features.forecast.gate import evaluate_gate
from app.features.forecast.monitor import DriftMonitor, compute_robust_z
from app.main import app


def test_features_no_leak(synthetic_data):
    prices_df, weather_df = synthetic_data
    leak_check(prices_df, weather_df, builder=build_all, n=6, seed=42)


def test_leaky_builder_caught(synthetic_data):
    prices_df, weather_df = synthetic_data

    def leaky_builder(p, w):
        f = build_all(p, w)
        f["ret1"] = f["lp"] - f["lp1"]
        return f

    with pytest.raises(AssertionError, match="LEAK"):
        leak_check(prices_df, weather_df, builder=leaky_builder, n=6, seed=42)


def test_gap_months_stay_missing(synthetic_data):
    prices_df, weather_df = synthetic_data
    f = build_all(prices_df, weather_df)

    m_june_2015 = to_m("2015-06")
    june_row = f[(f["commodity"] == "Maize") & (f["market"] == "Nairobi") & (f["m"] == m_june_2015)]

    assert not june_row.empty
    assert pd.isna(june_row.iloc[0]["lp1"])
    assert pd.isna(june_row.iloc[0]["y"])


def test_monitor():
    history = [0.05] * 30
    monitor = DriftMonitor(z_threshold=3.5, min_history=24, window=24)

    normal_res = monitor.check_error(0.052, history)
    assert not normal_res.is_alert

    shock_res = monitor.check_error(0.50, history)
    assert shock_res.is_alert
    assert shock_res.tier == "warning"

    alerts_df = pd.DataFrame([
        {"commodity": "Maize", "market": "Nairobi", "m": 100, "alert": True},
        {"commodity": "Maize", "market": "Kisumu", "m": 101, "alert": True},
        {"commodity": "Maize", "market": "Nakuru", "m": 102, "alert": True},
        {"commodity": "Beans", "market": "Nairobi", "m": 102, "alert": True},
    ])

    incidents = monitor.find_market_wide_incidents(alerts_df, lookback_months=3, min_markets=3)
    assert len(incidents) == 1
    assert incidents[0]["commodity"] == "Maize"
    assert len(incidents[0]["markets"]) == 3

    isolated_alerts_df = pd.DataFrame([
        {"commodity": "Maize", "market": "Nairobi", "m": 100, "alert": True},
    ])
    assert len(monitor.find_market_wide_incidents(isolated_alerts_df, lookback_months=3, min_markets=3)) == 0


def test_gate():
    years = [2016, 2017, 2018]
    records = []
    for y in years:
        for _ in range(20):
            records.append({
                "series": "Maize / Nairobi",
                "year": y,
                "actual": 100.0,
                "pred_champion": 110.0,
                "pred_challenger": 102.0,
            })
    df_promote = pd.DataFrame(records)
    res_promote = evaluate_gate(df_promote, min_improvement=0.03)
    assert res_promote.promoted is True

    records_equal = []
    for y in years:
        for _ in range(20):
            records_equal.append({
                "series": "Maize / Nairobi",
                "year": y,
                "actual": 100.0,
                "pred_champion": 110.0,
                "pred_challenger": 110.0,
            })
    df_equal = pd.DataFrame(records_equal)
    res_equal = evaluate_gate(df_equal, min_improvement=0.03)
    assert res_equal.promoted is False

    records_one_year = []
    for y in years:
        for _ in range(20):
            records_one_year.append({
                "series": "Maize / Nairobi",
                "year": y,
                "actual": 100.0,
                "pred_champion": 110.0,
                "pred_challenger": 101.0 if y == 2016 else 112.0,
            })
    df_one_year = pd.DataFrame(records_one_year)
    res_one_year = evaluate_gate(df_one_year, min_improvement=0.03)
    assert res_one_year.promoted is False


def test_api():
    client = TestClient(app, raise_server_exceptions=False)

    r_health = client.get("/health")
    assert r_health.status_code == 200

    r_series = client.get("/series")
    assert r_series.status_code == 200
    assert len(r_series.json()) == 11

    r_fc = client.get("/forecast?commodity=Maize&market=Nairobi&month=2017-03")
    assert r_fc.status_code == 200
    data = r_fc.json()
    assert data["commodity"] == "Maize"
    assert data["market"] == "Nairobi"
    assert data["champion"] == "naive"
    assert data["champion_forecast"] is not None
    assert data["challenger_forecast"] is not None

    r_404 = client.get("/forecast?commodity=FakeFood&market=Nairobi&month=2017-03")
    assert r_404.status_code == 404

    r_422 = client.get("/forecast?commodity=Maize&market=Nairobi&month=bad-month")
    assert r_422.status_code == 422

    r_metrics = client.get("/metrics")
    assert r_metrics.status_code == 200
    assert "forecast_abs_log_error" in r_metrics.text
