# Technical Innovation — Portfolio Reconstruction Engine

## 為什麼不只是 Landing Page

Landing Page 只能收表單；本引擎會把模糊的人類記憶轉為有可信度的結構化 Portfolio event，並能解釋每一步如何產生。

正式技術力集中在 FastAPI Python backend，不能把前端 JavaScript 計算當作最終成果。
目前 Python runtime 容納 deterministic finance calculation 與 Bedrock／fallback
orchestration；離線 training 已產生具版本、metrics 與 checksum 的 pre-scored JSON，
API 僅做 O(1) lookup，不安裝 sklearn。各能力透過 service boundary 分離。

```text
Stock Search
→ Entity Resolution
→ Month-level Temporal Alignment
→ Raw Price Envelope Validation
→ Corporate Action Adjustment
→ Reconstructed Return
→ Portfolio Fingerprint Vector
→ Explainable Persona
→ Confirmed Holding Gate
```

## 1. Entity Resolution

使用股票主檔將代號、名稱與產業對應到唯一 stock ID。熱門排序使用同學會瀏覽人數，只描述關注度，不等同推薦。

## 2. Temporal Price Envelope

將 243 個交易日聚合為每檔每月：

- 原始最低／最高價。
- 月末原始收盤。
- 月末還原收盤。
- adjustment factor。
- 公司行動旗標。

手動價格若不在該月 envelope 內即阻擋，讓「大概記得」仍能有基本資料品質。

## 3. Corporate Action Adjustment

使用者記得的是當時畫面上的原始成交價，但跨月份投報率必須處理拆股與除權息：

```text
factor = adjusted_close / raw_close
comparable_user_price = raw_user_price × factor
```

若月內 factor 變動超過 5%，標記 `corporateAction=true`，切分公司行動前後的 raw-price regimes，並禁止使用跨 regime 的模糊區間。實際價格必須先命中其中一個 regime，才套用該段 factor；正式產品再升級為交易日對應。

## 4. Portfolio Fingerprint

五維向量不是 LLM 猜測，而是從重建事件計算：進場位置、持有期、產業分散度、輸入精度、正規化報酬。人格只是此向量的可分享語言層。

正式版可用匿名且同意的歷史向量做 clustering，但 Demo 保持 deterministic mapping，確保評審可以重算。

## 5. Confirmed Holding Gate

測驗選股、歷史已賣出與目前仍持有是三種不同資料：

- `quiz_stock_interest`
- `reconstructed_trade`
- `confirmed_holding`

只有使用者明確選擇「仍持有」並同意保存時，才建立 confirmed holding。這避免把測驗答案污染正式 Portfolio。

## Implemented API surface（14 端點）

獲客（Time Machine，6）:

```text
GET  /api/v2/health
GET  /api/v2/stocks/search?q=台積
GET  /api/v2/stocks/popular?limit=12
GET  /api/v2/stocks/2330/months/2025-04/envelope
POST /api/v2/reconstructions/validate
POST /api/v2/reconstructions/complete      # 另回傳 report handle {report_id, claim_token}
```

留存（Portfolio Radar，6；session 驗證）:

```text
POST /api/v2/auth/session                          # 邀請碼 → session token
POST /api/v2/reports/{report_id}/claim
POST /api/v2/reports/{report_id}/confirmed-holdings # 唯一確認持股寫入路徑
GET  /api/v2/me/dashboard
POST /api/v2/me/action-cards/{card_id}/feedback
POST /api/v2/events/batch
```

AI Deep Dive（2；session + report ownership）：

```text
POST /api/v2/reports/{report_id}/ai-report
POST /api/v2/reports/{report_id}/questions
```

> 已移除（安全性）：舊的未驗證 `POST /api/v2/confirmed-holdings` 與
> `GET /api/v2/users/{user_id}/confirmed-holdings`（信任 client `user_id` 的跨會員
> 隔離漏洞）已刪除，改由上方 report-scoped 路徑寫入。

報酬、驗證與可信度必須由後端重算；LLM 只負責根據已驗證 vector 產生受 schema 限制的自然語言，不直接接收原始未驗證價格。

## Python 同環境，不同責任

| 實際模組 | 責任 | 是否可用 LLM |
|---|---|---|
| `repositories/market_data.py` | 檔案 catalog、搜尋與月份 envelope | 否 |
| `repositories/market_context.py` | 驗證並查詢 pre-scored JSON | 否 |
| `mindfolio-core/market/validation.py` | 精確價格與 company-action regime 驗證 | 否 |
| `mindfolio-core/market/reconstruction.py` | adjustment、報酬、confidence、vector、人格與分數 | 否 |
| `ai/narrative.py` + `fallback.py` | 將已驗證結果轉為 schema-valid 敘事 | 是 |
| `ai/deep_dive.py` | 結構化報告、fixed questions、guardrail/fallback | 是 |
| `services/reconstruction.py` + `repositories/holdings.py` | 重驗五檔並寫入 consented confirmed holdings | 否 |

AI 服務不可重新計算數字，也不可覆寫 persona code；LLM 失敗時使用固定模板，核心結果仍可正常回傳。

## AI training 的真正落點

V2 第一階段可用官方 2025 stock-month features 訓練：

- Market Regime clustering：辨識低波動累積、高波動反彈、籌碼同向或社群背離等情境。
- Market Anomaly detector：找出使用者買進月份相對異常的價格、成交、法人與社群組合。

價格亂填仍使用 deterministic envelope；persona 仍使用可重算 mapping。等有明確的 confirmed holding、share、radar enable 與 mute labels 後，再訓練股票／卡片排序模型。完整資料、模型與評估設計見 `10_AI_TRAINING_PLAN.md`。
