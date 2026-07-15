from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from mindfolio_core.features import MONTHLY_FEATURE_KEYS


PRICE_FILE = "01_Price_Valuation_2025.csv"
INSTITUTIONAL_FILE = "02_Institutional_Trading_2025.csv"
RETURN_FILE = "03_Return_Rate_2025.csv"
FORUM_FILE = "10_Forum_Posts_Replies_Daily_Stats_2025.csv"


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"股票代號": "string"}, encoding="utf-8-sig")


def _month_frame(frame: pd.DataFrame, date_column: str = "日期") -> pd.DataFrame:
    copy = frame.copy()
    copy[date_column] = pd.to_datetime(copy[date_column].astype(str), errors="raise")
    copy["month"] = copy[date_column].dt.to_period("M").astype(str)
    copy["stock_id"] = copy["股票代號"].astype(str).str.zfill(4)
    return copy.sort_values(["stock_id", date_column])


def build_monthly_features(data_dir: Path) -> pd.DataFrame:
    """Build one leakage-safe row per stock/month from the official data package."""
    price = _month_frame(_read_csv(data_dir / PRICE_FILE))
    returns = _month_frame(_read_csv(data_dir / RETURN_FILE))
    institutional = _month_frame(_read_csv(data_dir / INSTITUTIONAL_FILE))
    forum = _month_frame(_read_csv(data_dir / FORUM_FILE))

    adjusted = returns[["日期", "stock_id", "month", "還原收盤價"]].rename(
        columns={"還原收盤價": "adjusted_close"}
    )
    adjusted["daily_return"] = adjusted.groupby("stock_id")["adjusted_close"].pct_change(fill_method=None)

    def aggregate_adjusted(group: pd.DataFrame) -> pd.Series:
        values = group["adjusted_close"].astype(float)
        running_max = values.cummax()
        drawdown = values.div(running_max).sub(1)
        first = float(values.iloc[0])
        last = float(values.iloc[-1])
        return pd.Series(
            {
                "monthly_return": last / first - 1 if first else 0.0,
                "volatility": float(group["daily_return"].std(ddof=0) or 0.0),
                "max_drawdown": float(drawdown.min() or 0.0),
            }
        )

    market = adjusted.groupby(["stock_id", "month"], sort=True).apply(
        aggregate_adjusted, include_groups=False
    ).reset_index()

    price_monthly = price.groupby(["stock_id", "month"], as_index=False).agg(
        average_volume=("成交量", "mean"),
        total_volume=("成交量", "sum"),
        turnover=("週轉率(%)", "mean"),
    )
    price_monthly["volume_change"] = (
        price_monthly.groupby("stock_id")["average_volume"].pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
    )

    institutional_monthly = institutional.groupby(["stock_id", "month"], as_index=False).agg(
        institutional_net=("買賣超合計", "sum")
    )
    institution = institutional_monthly.merge(
        price_monthly[["stock_id", "month", "total_volume"]], on=["stock_id", "month"], how="inner"
    )
    institution["institutional_flow_ratio"] = institution["institutional_net"].div(
        institution["total_volume"].clip(lower=1)
    )

    forum["explicit_sentiment"] = forum["看多發文"].fillna(0) + forum["看空發文"].fillna(0)
    forum_monthly = forum.groupby(["stock_id", "month"], as_index=False).agg(
        post_count=("發文則數", "sum"),
        reply_count=("回文則數", "sum"),
        bullish_count=("看多發文", "sum"),
        bearish_count=("看空發文", "sum"),
        explicit_count=("explicit_sentiment", "sum"),
    )
    forum_monthly["community_heat"] = np.log1p(forum_monthly["post_count"] + forum_monthly["reply_count"])
    denominator = forum_monthly["bullish_count"] + forum_monthly["bearish_count"]
    forum_monthly["community_bullish_ratio"] = np.where(
        denominator >= 5,
        forum_monthly["bullish_count"].div(denominator.where(denominator.ne(0))),
        0.5,
    )

    features = market.merge(price_monthly, on=["stock_id", "month"], how="inner")
    features = features.merge(
        institution[["stock_id", "month", "institutional_net", "institutional_flow_ratio"]],
        on=["stock_id", "month"],
        how="inner",
    )
    features = features.merge(forum_monthly, on=["stock_id", "month"], how="inner")
    features["volume_change"] = features["volume_change"].fillna(0.0)
    features["turnover"] = features["turnover"].fillna(0.0)
    features = features.replace([np.inf, -np.inf], np.nan).dropna(subset=list(MONTHLY_FEATURE_KEYS))
    return features.sort_values(["stock_id", "month"]).reset_index(drop=True)
