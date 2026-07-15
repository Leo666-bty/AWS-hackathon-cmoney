# Mindfolio AI P0 最小整合規格

| 欄位 | 內容 |
|---|---|
| 文件狀態 | Implemented / Verified（deterministic 路徑；真實 Bedrock runtime 待驗） |
| 文件版本 | 2.0 |
| 更新日期 | 2026-07-15 |
| 適用範圍 | `V2/apps/web`、`V2/apps/api`、`V2/apps/ai-training`、`V2/packages/mindfolio-core`、`V2/infra/schema` |
| 目標 | 在既有 Time Machine → Portfolio Radar 流程中加入可驗證的市場情境與結構化 AI Deep Dive |

## 1. 決策摘要

P0 不改變既有 React + FastAPI + PostgreSQL 架構，也不建立線上 ML service。

```text
官方 2025 CSV
  ↓ 離線訓練
KMeans + IsolationForest
  ↓ 預先評分
版本化 market-context JSON
  ↓ API 啟動載入並 O(1) 查表
InvestmentAIContext
  ↓ Bedrock 或 deterministic fallback
結構化 AI Deep Dive + 三個固定證據型問題
```

責任邊界：

- deterministic reconstruction 是報酬、進場位置、人格與候選持股的金融真相來源。
- ML 只描述 `stock_id + YYYY-MM` 的歷史市場 regime 與 anomaly，不推論個人心理或未來行情。
- LLM 只解釋 API 已組好的 context，不讀原始 CSV、不自行計算、不提供買賣指令。
- 前端不新增自由聊天框，只呈現結構化報告與三個低門檻問題按鈕。

## 2. P0 範圍

### 2.1 必做

1. 月度 feature pipeline。
2. KMeans regime clustering。
3. IsolationForest anomaly detection。
4. 離線評估與版本化 pre-scored JSON artifact。
5. FastAPI artifact loader、版本／checksum 驗證與 fail-soft lookup。
6. 認領後 AI Deep Dive endpoint、cache 與 deterministic fallback。
7. 三個 server-side `question_id` 的證據型回答。
8. `/result` teaser 與 `/app` 完整結構化 UI。
9. migration、測試、build、lint 與文件對齊。

### 2.2 明確不做

- GMM、RAG、Vector DB、Multi-Agent、線上 sklearn inference。
- 自由文字聊天、截圖上傳、券商串接。
- 模型預測持股、成本、股數、焦慮或未來報酬。
- S3 artifact 自動刷新、模型服務拆分、即時串流。
- 為黑客松補齊正式產品等級的完整稽核與高可用架構。

## 3. Feature 與模型契約

### 3.1 Sample unit

```text
stock_id + YYYY-MM
```

### 3.2 Feature version

`monthly-features-v1`：

```text
monthly_return
volatility
max_drawdown
volume_change
turnover
institutional_flow_ratio
community_heat
community_bullish_ratio
```

規則：

- `institutional_flow_ratio` 使用法人淨流量除以成交量，避免公司規模直接支配 clustering。
- 連續特徵以 robust scaling 處理；極端值 winsorize，參數寫入 metadata。
- 社群看多比例只代表全站市場情緒，不代表 LEO 個人情緒。
- 任何 feature 只使用目標月份當下或之前資料，避免 future leakage。
- `salient_feature_keys` 是相對偏離最大的可觀測特徵，不宣稱因果或 feature importance。

### 3.3 模型

| 任務 | 模型 | P0 決策 |
|---|---|---|
| Market regime | KMeans | 固定 random seed；以 silhouette、cluster size 與人工可解釋性驗證 |
| Market anomaly | IsolationForest | 產生 anomaly percentile；UI 僅顯示一般／注意／顯著 |

`regime_match` 只能稱為 `strong / moderate / weak` 的群集相似程度，不稱為預測機率。

## 4. Runtime Artifact

API 不載入 sklearn/joblib。訓練流程將所有月份預先評分後輸出：

```text
V2/data/market-context-2025-v1.json
```

核心格式：

```json
{
  "metadata": {
    "model_version": "2025-v1",
    "feature_version": "monthly-features-v1",
    "training_range": ["2025-01-01", "2025-12-31"],
    "feature_keys": [],
    "sample_count": 3584,
    "preprocessing": {},
    "metrics": {},
    "generated_at": "ISO-8601"
  },
  "contexts": {
    "2330:2025-04": {
      "stock_id": "2330",
      "month": "2025-04",
      "regime_id": 2,
      "regime_label": "高波動修復",
      "regime_match": "strong",
      "anomaly_level": "attention",
      "anomaly_score": 0.89,
      "salient_feature_keys": ["volatility", "institutional_flow_ratio"],
      "evidence": {},
      "feature_version": "monthly-features-v1",
      "model_version": "2025-v1",
      "source_as_of": "2025-12-31"
    }
  },
  "content_sha256": "sha256-of-contexts"
}
```

Runtime 規則：

- API 啟動時驗證 schema、`feature_version` 與 `content_sha256`。
- lookup key 是 `stock_id:YYYY-MM`，查找複雜度 O(1)。
- artifact 缺失、損壞、版本不符時 API 仍可啟動，health 標記 unavailable。
- 無對應月份時只略過該筆 market context，不影響原本 reconstruction。

## 5. AI Deep Dive 契約

### 5.1 生成條件

- 僅限已登入會員存取已由自己 claim 的 report。
- 第一次開啟時生成；相同 cache key 直接重用。
- cache key 至少包含 context schema、feature、model 與 prompt version。
- Bedrock 失敗、timeout 或 guardrail 不通過時，回傳 deterministic fallback。

### 5.2 結構化輸出

禁止讓前端解析一整段 Markdown。API 回傳：

```text
title
executive_summary
strengths[]
watchouts[]
market_moments[]
suggested_questions[]
source = bedrock | fallback
versions
generated_at
```

每個段落包含 `body` 與 `evidence_refs[]`。所有 evidence ref 必須存在於 server 組好的 `InvestmentAIContext`。

### 5.3 固定問題 ID

P0 只接受：

| question_id | UI 標籤 |
|---|---|
| `why-persona` | 為什麼我是這種投資人格？ |
| `most-influential-trade` | 哪筆交易最影響結果？ |
| `why-anomalous-month` | 哪個買進月份最不尋常？ |

不接受自由文字，避免 prompt injection、成本失控與聊天低使用率問題。

### 5.4 Guardrail

- 不得包含買進、賣出、加碼、減碼、目標價、保證獲利等指令。
- 不得把群集結果包裝成真實人格診斷。
- 不得把全站社群情緒描述成 LEO 的個人情緒。
- 不得使用 context 以外的數字或證據。

## 6. API 與資料庫

新增 endpoint：

```http
POST /api/v2/reports/{report_id}/ai-report
POST /api/v2/reports/{report_id}/questions
```

兩者都沿用 invite session 與 report ownership，不接受前端傳入 `user_id`。

`reconstruction_reports` 新增：

```text
ai_report JSONB
ai_report_cache_key TEXT
ai_report_generated_at TIMESTAMPTZ
```

不持久化另一份重複的 `ai_context`；生成時由 report result + runtime market context 即時組裝。

## 7. 前端

### `/result`

只顯示 teaser：認領後可解鎖買進月份市場情境與三個證據型追問，不提前產生 Bedrock 成本。

### `/app`

Portfolio Radar 保持原本主流程，新增可展開的 AI Deep Dive：

1. 使用者主動點擊「產生 AI 深度解讀」。
2. 顯示 loading、錯誤與 fallback 狀態。
3. 呈現摘要、優勢、觀察點、歷史市場時刻。
4. 顯示三個問題 chips；點擊後只送 `question_id`。
5. 回答保留 evidence refs 與限制聲明。

追蹤事件：

```text
ai_report_open
ai_report_generated
ai_question_chip_click
ai_answer_rendered
ai_answer_fallback
```

## 8. P0 驗收條件

- [x] 官方 CSV 可重建 3,584 筆月度 features，且 feature contract 有測試。
- [x] 訓練流程輸出真實 metrics、版本與 checksum，不使用虛構數字。
- [x] API runtime image 不需要 sklearn。
- [x] artifact 缺失或損壞不影響原本主流程。
- [x] 非 report owner 無法存取 AI report 或 question answer。
- [x] 相同 cache key 不重複呼叫 Bedrock。
- [x] 前端無自由聊天框，問題只以三個 ID 提交。
- [x] Bedrock 不可用時仍能完成可展示的 deterministic flow。
- [x] Python tests、React tests、lint、build 全部通過。
- [x] `07`、`09`、`10`、`11`、`12` 與 README 最終狀態一致。

## 9. 最小部署拓撲

```text
單機 EC2（Docker Compose，見 11_DEPLOYMENT）
  ├─ nginx web（React static build + reverse-proxy /api → api）
  ├─ FastAPI（載入 pre-scored JSON）
  └─ PostgreSQL（report + AI-report cache）
        ↓ optional
Amazon Bedrock
```

P0 的模型更新是 release-time build step，不是 runtime 自動訓練。正式產品才評估 S3 model registry、排程重訓與獨立 inference service。
