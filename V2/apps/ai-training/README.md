# AI Training

P0 offline training 已完成：由官方 2025 CSV 建立 3,584 個 stock-month features，訓練 KMeans 與 IsolationForest，並輸出版本化、具 checksum 的 pre-scored runtime JSON。FastAPI 不載入 sklearn/joblib。

目前能力：

1. stock-month feature table
2. KMeans Market Regime baseline
3. IsolationForest Market Anomaly baseline
4. artifact evaluation and publishing

```bash
V2/.venv/bin/python -m mindfolio_training.pipeline \
  --data-dir V2/data/Delivery_Hackathon_DataPackage_20260624 \
  --features-output V2/apps/ai-training/artifacts/monthly-features-v1.csv \
  --artifact-output V2/data/market-context-2025-v1.json \
  --model-output V2/apps/ai-training/artifacts/market-models-2025-v1.joblib
```

`artifacts/` 內的 features 與 joblib 為可重建輸出、不提交；API 使用的
`V2/data/market-context-2025-v1.json` 隨 release 版本化。
