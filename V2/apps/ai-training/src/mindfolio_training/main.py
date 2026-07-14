import json

from mindfolio_core.features import FEATURE_VERSION, MONTHLY_FEATURE_KEYS


def main() -> None:
    print(
        json.dumps(
            {
                "status": "initialized",
                "feature_version": FEATURE_VERSION,
                "feature_count": len(MONTHLY_FEATURE_KEYS),
                "planned_models": ["market-regime-kmeans", "market-anomaly-isolation-forest"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
