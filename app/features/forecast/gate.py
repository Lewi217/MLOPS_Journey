from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Sequence

import numpy as np
import pandas as pd

MIN_IMPROVEMENT_THRESHOLD: Final[float] = 0.03


@dataclass(frozen=True)
class GateEvaluationResult:
    promoted: bool
    champ_mape: float
    challenger_mape: float
    relative_improvement: float
    years_evaluated: list[int]
    years_won_by_challenger: list[int]
    reason: str


def evaluate_gate(
    predictions_df: pd.DataFrame,
    min_improvement: float = MIN_IMPROVEMENT_THRESHOLD,
    actual_col: str = "actual",
    champ_col: str = "pred_champion",
    challenger_col: str = "pred_challenger",
) -> GateEvaluationResult:
    clean = predictions_df.dropna(subset=[actual_col, champ_col, challenger_col]).copy()
    if clean.empty:
        return GateEvaluationResult(
            promoted=False,
            champ_mape=float("nan"),
            challenger_mape=float("nan"),
            relative_improvement=0.0,
            years_evaluated=[],
            years_won_by_challenger=[],
            reason="No overlapping predictions to compare",
        )

    clean["champ_ape"] = np.abs(clean[champ_col] - clean[actual_col]) / clean[actual_col]
    clean["chal_ape"] = np.abs(clean[challenger_col] - clean[actual_col]) / clean[actual_col]

    champ_series_mapes = clean.groupby("series")["champ_ape"].mean()
    chal_series_mapes = clean.groupby("series")["chal_ape"].mean()

    champ_mape = float(champ_series_mapes.mean())
    chal_mape = float(chal_series_mapes.mean())

    if champ_mape <= 0:
        rel_improvement = 0.0
    else:
        rel_improvement = (champ_mape - chal_mape) / champ_mape

    years_evaluated: list[int] = sorted(clean["year"].unique())
    years_won: list[int] = []

    for yr in years_evaluated:
        yr_df = clean[clean["year"] == yr]
        yr_champ = yr_df["champ_ape"].mean()
        yr_chal = yr_df["chal_ape"].mean()
        if yr_chal < yr_champ:
            years_won.append(int(yr))

    majority_years = len(years_won) > (len(years_evaluated) / 2.0)
    clears_threshold = rel_improvement >= min_improvement

    if clears_threshold and majority_years:
        promoted = True
        reason = (
            f"Challenger improved MAPE by {rel_improvement * 100:.2f}% (>= {min_improvement * 100:.1f}%) "
            f"and won {len(years_won)}/{len(years_evaluated)} years."
        )
    elif not clears_threshold:
        promoted = False
        reason = (
            f"Improvement of {rel_improvement * 100:.2f}% did not meet {min_improvement * 100:.1f}% threshold."
        )
    else:
        promoted = False
        reason = (
            f"Challenger improved MAPE by {rel_improvement * 100:.2f}%, but only won {len(years_won)}/{len(years_evaluated)} years."
        )

    return GateEvaluationResult(
        promoted=promoted,
        champ_mape=round(champ_mape * 100, 2),
        challenger_mape=round(chal_mape * 100, 2),
        relative_improvement=round(rel_improvement, 4),
        years_evaluated=years_evaluated,
        years_won_by_challenger=years_won,
        reason=reason,
    )
