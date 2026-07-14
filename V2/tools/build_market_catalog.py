"""Build the V2 browser database snapshot from the organizer's 2025 CSV files."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "V2" / "data" / "Delivery_Hackathon_DataPackage_20260624"
OUTPUT = ROOT / "V2" / "demo" / "market-data.js"
JSON_OUTPUT = ROOT / "V2" / "data" / "market-catalog.json"


def number(value: Optional[str], default: float = 0.0) -> float:
    try:
        return float(value or default)
    except ValueError:
        return default


def read_wide_table() -> dict[str, dict]:
    result: dict[str, dict] = {}
    with (SOURCE / "09_Wide_Table_Summary_One_Row_Per_Stock_2025.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        for row in csv.DictReader(handle):
            result[row["股票代號"]] = {
                "id": row["股票代號"],
                "name": row["股票名稱"],
                "industry": row["產業"] or "其他",
                "views": int(number(row.get("同學會瀏覽人數"))),
            }
    return result


def read_adjustment_factors() -> dict[tuple[str, str], float]:
    factors: dict[tuple[str, str], float] = {}
    with (SOURCE / "03_Return_Rate_2025.csv").open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            raw_key = (row["股票代號"], row["日期"])
            factors[raw_key] = number(row["還原收盤價"])
    return factors


def build() -> dict:
    stocks = read_wide_table()
    adjusted_close = read_adjustment_factors()
    monthly: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))

    with (SOURCE / "01_Price_Valuation_2025.csv").open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            stock_id = row["股票代號"]
            date = row["日期"]
            raw_close = number(row["收盤價"])
            adjusted = adjusted_close.get((stock_id, date), raw_close)
            factor = adjusted / raw_close if raw_close else 1.0
            monthly[stock_id][date[4:6]].append(
                {
                    "date": date,
                    "low": number(row["最低價"]),
                    "high": number(row["最高價"]),
                    "close": raw_close,
                    "adjusted": adjusted,
                    "factor": factor,
                }
            )

    ranked = sorted(stocks.values(), key=lambda stock: stock["views"], reverse=True)
    popular_ids = {stock["id"] for stock in ranked[:12]}
    output_stocks = []

    for stock_id, stock in sorted(stocks.items()):
        month_values = {}
        for month, records in sorted(monthly[stock_id].items()):
            records.sort(key=lambda record: record["date"])
            regime_records = []
            current_regime = []
            for record in records:
                if current_regime:
                    baseline = current_regime[-1]["factor"]
                    ratio = record["factor"] / max(baseline, 0.000001)
                    if ratio > 1.05 or ratio < 0.95:
                        regime_records.append(current_regime)
                        current_regime = []
                current_regime.append(record)
            if current_regime:
                regime_records.append(current_regime)
            regimes = [
                {
                    "low": round(min(record["low"] for record in regime), 2),
                    "high": round(max(record["high"] for record in regime), 2),
                    "factor": round(regime[-1]["factor"], 8),
                }
                for regime in regime_records
            ]
            month_values[month] = {
                "low": round(min(record["low"] for record in records), 2),
                "high": round(max(record["high"] for record in records), 2),
                "close": round(records[-1]["close"], 2),
                "adjustedClose": round(records[-1]["adjusted"], 4),
                "factor": round(records[-1]["factor"], 8),
                "corporateAction": len(regimes) > 1,
                "regimes": regimes,
            }
        output_stocks.append(
            {
                **stock,
                "popular": stock_id in popular_ids,
                "months": month_values,
            }
        )

    return {
        "asOf": "2025-12-31",
        "source": "CMoney Hackathon 2025 price and adjusted-return package",
        "stockCount": len(output_stocks),
        "monthEnvelopeCount": sum(len(stock["months"]) for stock in output_stocks),
        "popular": [stock["id"] for stock in ranked[:12]],
        "stocks": output_stocks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        nargs="?",
        const=str(JSON_OUTPUT),
        default=None,
        metavar="PATH",
        help=(
            "Also write a pure JSON catalog for the backend to read "
            f"(default: {JSON_OUTPUT})."
        ),
    )
    args = parser.parse_args()

    catalog = build()
    payload = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"))

    OUTPUT.write_text(f"const MARKET_DATABASE = {payload};\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(payload)} bytes)")

    if args.json is not None:
        json_path = Path(args.json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(payload + "\n", encoding="utf-8")
        print(f"Wrote {json_path} ({len(payload)} bytes)")


if __name__ == "__main__":
    main()
