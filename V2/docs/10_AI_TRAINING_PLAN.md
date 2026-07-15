# AI Training Plan

> Online product integration、完整 AI 報告與問答契約以
> [`14_AI_MINIMAL_INTEGRATION_SPEC.md`](14_AI_MINIMAL_INTEGRATION_SPEC.md) 為準；本文件維持 training strategy 的 source of truth。

## 目標

V2 的 AI training 不用來猜使用者真實持股、預測未來獲利或判定心理人格。可落地的訓練任務分成兩層：

1. **現在可做**：用主辦方 2025 市場資料訓練 Market Regime／Anomaly 模型，替 Portfolio Time Machine 增加可量化的歷史情境。
2. **累積用戶標籤後再做**：用明確的完成、確認持股、分享與回訪事件訓練排序模型。

AI narrative 使用 Bedrock／LLM 生成文案，但這是 inference orchestration，不應包裝成自行訓練大型語言模型。

## 現有資料能支撐什麼

主辦方資料約有 300 檔股票、2025 年每日市場資料；目前 pipeline 實際產出 3,584 個完整 stock-month samples。

| 資料 | 可建立的 features |
|---|---|
| 價格與報酬 | 月報酬、波動、最大回落、距高低點、momentum |
| 成交量／週轉率 | volume change、turnover anomaly |
| 法人買賣 | 外資、投信、自營商月累積與方向一致性 |
| 估值／股利 | PE、PB、yield、valuation bucket |
| 社群彙總 | 發回文熱度、明確多空比例、熱度變化 |
| 產業分類 | industry one-hot／target encoding |

現有資料沒有：真實 member ID、個人持股 ground truth、實際交易紀錄、測驗轉換事件。因此第一版不能訓練「誰真的持有哪檔」或「誰投資能力比較好」。

## Training Level 0：Deterministic baseline

正式訓練前先保留可重算基準：

- 價格 envelope validation。
- company-action regimes。
- reconstructed return。
- confidence score。
- deterministic Portfolio Fingerprint 與 persona mapping。

這些規則不需要 ML，且必須作為模型 fallback 與比較基準。

## Training Level 1：現在可實作

### Model A — Market Regime Clustering

目的：把每個 stock-month 分成可解釋的歷史市場情境，例如：

- 低波動累積。
- 高波動反彈。
- 法人與價格同向。
- 社群過熱但法人背離。
- 景氣循環回落。

建議第一版：

```text
Monthly Feature Builder
→ missing-value handling
→ RobustScaler + 1%/99% winsorization
→ KMeans（k=3..6 candidates）
→ cluster balance gate + silhouette selection
→ analyst-readable cluster naming
```

Cluster 名稱由分析規則或 Bedrock 根據 cluster centroid 產生候選描述，再由團隊確認；不能讓 LLM 任意改變 cluster assignment。

### Model B — Market Anomaly Detector

目的：找出某檔股票在某月相對自身與市場異常的時刻，提供「為什麼這個月值得回看」的技術 Output。

建議第一版使用 `IsolationForest`：

- Input：報酬、波動、volume、turnover、法人、社群熱度與背離 features。
- Output：`anomaly_score`、top contributing feature hints、model version。
- UI：只顯示一般／注意／顯著與證據，不直接顯示難以理解的原始 score。

價格亂填仍使用 deterministic envelope，不使用 anomaly model 取代明確規則。

### Portfolio aggregation

五檔股票完成重建後，FastAPI 將每檔買進月對應到 regime 與 anomaly：

```text
trade reconstruction
→ stock-month pre-scored JSON lookup
→ five-stock regime distribution
→ anomaly-weighted portfolio context
→ Portfolio Fingerprint
→ AI narrative
```

這會讓結果不只說「你低接或長抱」，還能說：

> 你的五次進場有三次發生在高波動反彈 regime，其中兩次同時出現法人與社群背離。

## Training Level 2：有用戶事件後

### Stock candidate ranking

目的：決定陌生用戶下一個最可能願意確認的股票，而不是直接猜成真實持股。

Features：

- 搜尋、查看、加入五檔、完成重建等事件。
- 股票熱度、產業與 market regime。
- 使用者已確認產業分布。
- 卡片曝光次數與 interruption cost。

Labels：

- Positive：使用者明確確認 `holding`。
- Negative：明確選擇 `sold`／`irrelevant`，或在足夠曝光後拒絕。
- Unlabeled：只查看但未回答；不得直接當 negative。

第一版可用 Logistic Regression／Gradient Boosting ranking baseline，評估 Precision@K、Recall@K、NDCG 與 calibration。

### Result／card ranking

目的：選擇哪一個歷史情境或持股提醒最值得先顯示。

Labels：`result_open`、`evidence_open`、`share`、`radar_enable`、`mute`。模型優化的是內容排序，不是交易方向。

## Training Level 3：資料量足夠後

### User portfolio clustering

當有足夠且經同意的 Portfolio Fingerprint vectors，可做 unsupervised clustering，觀察 deterministic 八型是否需要調整。

必須檢查：

- cluster stability。
- 產業或資產規模是否造成偏誤。
- 新資料加入後 persona 是否頻繁跳動。
- 每個 cluster 是否能用使用者看得懂的證據解釋。

在此之前，Demo 保持 deterministic persona，不能用 synthetic data 宣稱發現真實用戶族群。

## 不建議訓練的項目

- 用 2025 單年資料預測未來買賣點。
- 用五檔測驗結果判斷真實投資能力。
- 從市場社群資料推論個人焦慮或風險人格。
- 用未確認的搜尋／瀏覽直接當持股 ground truth。
- 為了黑客松微調大型語言模型；成本高且沒有合格 label set。

## Python project boundary（已實作）

`apps/ai-training` 已包含 feature builder 與訓練／發布 pipeline；runtime DTO 由
`mindfolio-core/inference` 共用。

```text
apps/ai-training/
├── src/mindfolio_training/
│   ├── features.py
│   └── pipeline.py
└── tests/

packages/mindfolio-core/
├── features/                  # API 與 training 共用 feature definitions
├── inference/                 # artifact loading 與 predict contracts
└── domain/                    # reconstruction deterministic logic
```

FastAPI 與 AI training 開發時使用同一個 Python virtual environment；production API image 不安裝 pandas、sklearn 或 training package：

- `apps/api`：載入 pre-scored JSON 並提供 HTTP requests。
- `apps/ai-training`：offline batch training。
- `mindfolio-core`：兩者共用，避免 training-serving skew。

## Model artifact contract

每個 artifact 至少保存：

```json
{
  "model_name": "market-regime-kmeans",
  "model_version": "2025-v1",
  "feature_version": "monthly-features-v1",
  "training_range": ["2025-01-01", "2025-12-31"],
  "sample_count": 3584,
  "metrics": {
    "silhouette": 0.0,
    "stability": 0.0
  },
  "generated_at": "ISO-8601"
}
```

數值只是 schema placeholder，沒有實際訓練前不可填入虛構成績。

## FastAPI runtime boundary

FastAPI 啟動時只載入已核准的 `data/market-context-2025-v1.json`：

```text
MarketContextRepository.get(stock_id, month)
→ regime_id
→ anomaly_level
→ evidence feature keys
→ model_version
```

- Request path 不執行 training，也不載入 sklearn/joblib。
- Artifact 不存在或版本不符時回到 deterministic rules。
- Model output 不直接寫入 confirmed holding。
- AI narrative 只能使用已驗證 inference DTO。

## Evaluation

| 模型 | Offline metrics | Online validation |
|---|---|---|
| Regime clustering | silhouette、cluster stability、centroid interpretability | 使用者是否理解／展開情境 |
| Anomaly detector | time-split stability、人工 precision review | evidence open、dismiss rate |
| Stock ranking | Precision@K、NDCG、calibration | confirmed holding uplift |
| Card ranking | NDCG、coverage、interruption penalty | result open、radar enable、mute |

所有 supervised model 必須使用時間切分，避免把未來資料洩漏到過去情境。

## 黑客松可展示的最小 Training Demo

1. 從官方 CSV 建立 stock-month feature table。
2. 訓練 KMeans regime baseline 與 IsolationForest anomaly baseline。
3. 預先評分全部月份，保存 metadata、真實 metrics 與 checksum。
4. FastAPI 對五檔買進月份執行 O(1) lookup。
5. React `/app` 顯示結構化 AI Deep Dive、歷史市場時刻與三個固定問題。
6. Bedrock 只把已驗證結果寫成自然語言；斷線時顯示固定模板。

這條路徑同時展示資料工程、ML training、FastAPI inference、React visualization 與生成式 AI，但不需要虛構個人持股模型。
