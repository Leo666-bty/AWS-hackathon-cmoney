from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {
    "stock_id",
    "date",
    "close",
    "institutional_net",
    "bullish_count",
    "bearish_count",
    "post_count",
    "reply_count",
}


def _rolling_zscore(series: pd.Series, window: int = 20) -> pd.Series:
    mean = series.rolling(window, min_periods=5).mean()
    std = series.rolling(window, min_periods=5).std(ddof=0).replace(0, np.nan)
    return ((series - mean) / std).fillna(0.0)


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing normalized columns: {sorted(missing)}")

    result = frame.copy()
    result["date"] = pd.to_datetime(result["date"], errors="raise")
    result = result.sort_values(["stock_id", "date"]).reset_index(drop=True)
    grouped = result.groupby("stock_id", group_keys=False)

    result["return_1d"] = grouped["close"].pct_change().fillna(0.0)
    result["return_5d"] = grouped["close"].pct_change(5).fillna(0.0)
    result["institutional_net_20d"] = grouped["institutional_net"].transform(
        lambda value: value.rolling(20, min_periods=1).sum()
    )
    result["institutional_net_z20"] = grouped["institutional_net"].transform(_rolling_zscore)
    result["post_count_z20"] = grouped["post_count"].transform(_rolling_zscore)
    result["reply_count_z20"] = grouped["reply_count"].transform(_rolling_zscore)

    bullish_7d = grouped["bullish_count"].transform(lambda value: value.rolling(7, min_periods=1).sum())
    bearish_7d = grouped["bearish_count"].transform(lambda value: value.rolling(7, min_periods=1).sum())
    explicit_total = (bullish_7d + bearish_7d).replace(0, np.nan)
    result["community_bullish_ratio_7d"] = (bullish_7d / explicit_total).fillna(0.5)

    institution_direction = np.sign(result["institutional_net_20d"])
    community_direction = np.sign(result["community_bullish_ratio_7d"] - 0.5)
    result["institution_community_divergence"] = (institution_direction != community_direction).astype(float)
    result["date"] = result["date"].dt.strftime("%Y-%m-%d")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Build normalized rolling market-moment features.")
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()

    output = build_features(pd.read_csv(args.input_csv))
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output_csv, index=False)


if __name__ == "__main__":
    main()
