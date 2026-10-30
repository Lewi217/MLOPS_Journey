from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Sequence

import numpy as np
import pandas as pd

DEFAULT_MIN_HISTORY: Final[int] = 24
DEFAULT_WINDOW: Final[int] = 24
DEFAULT_Z_ALERT: Final[float] = 3.5
MARKETWIDE_MIN_MARKETS: Final[int] = 3
MARKETWIDE_WINDOW_MONTHS: Final[int] = 3


def compute_robust_z(
    abs_errors: Sequence[float] | np.ndarray,
    min_history: int = DEFAULT_MIN_HISTORY,
    window: int = DEFAULT_WINDOW,
) -> list[float]:
    arr = np.asarray(abs_errors, dtype=float)
    z_scores: list[float] = []

    for i, err in enumerate(arr):
        if i < min_history or np.isnan(err):
            z_scores.append(float("nan"))
            continue

        start_idx = max(0, i - window)
        h = arr[start_idx:i]
        h_clean = h[~np.isnan(h)]

        if len(h_clean) < min_history:
            z_scores.append(float("nan"))
            continue

        med = float(np.median(h_clean))
        mad = float(np.median(np.abs(h_clean - med)))
        spread = max(1.4826 * mad, 0.01)

        z = (err - med) / spread
        z_scores.append(float(z))

    return z_scores


@dataclass(frozen=True)
class AlertResult:
    is_alert: bool
    z_score: Optional[float]
    tier: str
    message: str


class DriftMonitor:
    def __init__(
        self,
        z_threshold: float = DEFAULT_Z_ALERT,
        min_history: int = DEFAULT_MIN_HISTORY,
        window: int = DEFAULT_WINDOW,
    ) -> None:
        self.z_threshold = z_threshold
        self.min_history = min_history
        self.window = window

    def check_error(
        self,
        current_abs_error: float,
        error_history: Sequence[float],
    ) -> AlertResult:
        full_seq = list(error_history) + [current_abs_error]
        z_list = compute_robust_z(
            full_seq,
            min_history=self.min_history,
            window=self.window,
        )
        current_z = z_list[-1]

        if np.isnan(current_z):
            return AlertResult(
                is_alert=False,
                z_score=None,
                tier="none",
                message="Insufficient error history to evaluate drift",
            )

        if current_z >= self.z_threshold:
            return AlertResult(
                is_alert=True,
                z_score=round(current_z, 2),
                tier="warning",
                message=f"Series error drift detected (robust z={current_z:.2f} >= {self.z_threshold})",
            )

        return AlertResult(
            is_alert=False,
            z_score=round(current_z, 2),
            tier="none",
            message="Error within expected distribution",
        )

    def find_market_wide_incidents(
        self,
        alerts_df: pd.DataFrame,
        lookback_months: int = MARKETWIDE_WINDOW_MONTHS,
        min_markets: int = MARKETWIDE_MIN_MARKETS,
    ) -> list[dict[str, Any]]:
        incidents: list[dict[str, Any]] = []
        if alerts_df.empty or "alert" not in alerts_df.columns:
            return incidents

        flagged_alerts = alerts_df[alerts_df["alert"]].copy()
        if flagged_alerts.empty:
            return incidents

        for commodity, group in flagged_alerts.groupby("commodity"):
            min_m = int(group["m"].min())
            max_m = int(group["m"].max())

            active_episode: Optional[dict[str, Any]] = None

            for m in range(min_m, max_m + 1):
                window_alerts = group[(group["m"] <= m) & (group["m"] > m - lookback_months)]
                markets_in_window = sorted(window_alerts["market"].unique())

                if len(markets_in_window) >= min_markets:
                    if active_episode is None:
                        active_episode = {
                            "commodity": commodity,
                            "first_m": m,
                            "last_m": m,
                            "markets": set(markets_in_window),
                        }
                    else:
                        active_episode["last_m"] = m
                        active_episode["markets"].update(markets_in_window)
                else:
                    if active_episode is not None:
                        incidents.append({
                            "commodity": active_episode["commodity"],
                            "first_month_m": active_episode["first_m"],
                            "last_month_m": active_episode["last_m"],
                            "markets": sorted(active_episode["markets"]),
                        })
                        active_episode = None

            if active_episode is not None:
                incidents.append({
                    "commodity": active_episode["commodity"],
                    "first_month_m": active_episode["first_m"],
                    "last_month_m": active_episode["last_m"],
                    "markets": sorted(active_episode["markets"]),
                })

        return incidents
