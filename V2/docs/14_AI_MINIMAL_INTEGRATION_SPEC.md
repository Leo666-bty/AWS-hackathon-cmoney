# Mindfolio AI 最小改動整合需求規格

| 欄位 | 內容 |
|---|---|
| 文件狀態 | Planned |
| 文件版本 | 1.0 |
| 更新日期 | 2026-07-15 |
| 適用範圍 | `V2/apps/web`、`V2/apps/api`、`V2/apps/ai-training`、`V2/packages/mindfolio-core` |
| 前置文件 | `10_AI_TRAINING_PLAN.md`、`12_V2_END_TO_END_SPEC.md`、`13_ACQUISITION_RETENTION_INTEGRATION_SPEC.md` |

## 1. 決策摘要

本需求在**不改變現有 React + FastAPI + `mindfolio-core` + PostgreSQL 架構**的前提下，補齊目前專案的 AI 價值鏈：

```text
使用者輸入五檔交易記憶
        ↓
既有 deterministic reconstruction
        ↓
既有 Investment DNA／分數／持股候選
        ↓
新增：Market Regime + Anomaly inference
        ↓
新增：認領後的完整 AI 投資報告
        ↓
新增：以報告為 Context 的證據型問答
        ↓
既有 Portfolio Radar 與互動事件
```

核心分工維持：

- **金融計算引擎負責事實**：報酬、進場位置、掌握程度、資料信心、人格與持股候選。
- **ML 負責歷史市場情境**：辨識使用者買進月份所處的 regime 與 anomaly，不判定個人心理或未來報酬。
- **LLM 負責解釋**：把已驗證的個人結果與市場情境生成完整 Markdown 報告，並回答與該報告相關的問題。
- **前端負責低門檻體驗**：不把聊天放在入口；先產生結果，再以三個建議問題或選填文字問題進一步探索。

## 2. 現況盤點

### 2.1 已存在且必須沿用

| 能力 | 現有路徑 | 狀態 |
|---|---|---|
| 五檔股票與模糊交易記憶輸入 | `apps/web/src/routes/` | 已實作 |
| 行情 envelope 與交易重建 | `packages/mindfolio-core/` | 已實作，金融真相來源 |
| 人格、指紋、分數與持股候選 | `ReconstructionResult` | 已實作，deterministic |
| 短版 AI narrative 與 fallback | `apps/api/src/mindfolio_api/ai/` | 已實作 |
| 匿名報告、認領與持股同意 | `reconstruction_reports`、retention router | 已實作 |
| Portfolio Radar、行動卡與事件追蹤 | `/api/v2/me/dashboard`、`interaction_events` | 已實作 |
| AI training package boundary | `apps/ai-training/` | 已初始化，尚未訓練模型 |
| 月度 feature contract | `mindfolio_core.features` | 已定義 `monthly-features-v1` |

### 2.2 現有缺口

1. `apps/ai-training` 只有 scaffold，沒有可部署 artifact 與實際評估結果。
2. FastAPI 尚未把 model inference 接入 reconstruction/report context。
3. 現有 Bedrock narrative 只有三個短欄位，不足以形成可解鎖的完整 Investment DNA 報告。
4. Portfolio Radar 的 suggested questions 目前只觸發 UI 顯示，沒有真正的 context-aware AI answer。
5. 官方市場、法人與社群資料尚未完整呈現在使用者個人報告的證據鏈中。

## 3. 產品需求

### 3.1 使用者價值

使用者不需要上傳截圖、連結券商或先與 AI 對話，只需完成現有 Time Machine 流程，即可獲得：

1. 依歷史交易重建的 Investment DNA。
2. 買進當時的市場 regime、異常程度與可驗證證據。
3. 認領後解鎖的完整個人投資 Markdown 報告。
4. 對報告內容提出簡單問題，取得有引用依據的個人化解釋。

### 3.2 低門檻原則

- 不新增前置心理量表。
- 不新增截圖上傳或券商串接。
- 不要求使用者先開放式聊天。
- 完整報告與問答都放在既有結果之後，不阻擋 acquisition funnel。
- 預設提供三個問題按鈕，文字輸入為選填。
- 每次回答只依現有報告與市場證據，不要求使用者重複輸入持股。

### 3.3 AI 報告解鎖流程

```text
/result 顯示短版人格與 AI narrative
        ↓
使用者進入 /activate
        ↓
既有 claim report + confirmed holdings
        ↓
/app 顯示「完整 AI 投資報告」
        ↓
首次開啟時生成或讀取 cache
        ↓
顯示 Markdown 報告 + 建議問題
```

完整報告是註冊／認領後價值，不應在匿名 result 階段完整揭露。匿名頁只顯示 teaser，例如核心人格、其中一項優勢與一項待解鎖洞察。

## 4. AI 與資料的正確邊界

### 4.1 可以推論

- 使用者輸入交易在 2025 歷史行情中的重建報酬。
- 相對該檔股票月度區間的進場位置與資料精度。
- 五檔組合呈現的 deterministic Investment DNA。
- 買進月份所處的市場 regime。
- 該股票月份是否屬於市場異常情境。
- 持股產業分布、事件證據與歷史市場背景。

### 4.2 不可宣稱

- 使用者真實心理風險承受度或臨床焦慮程度。
- 使用者投資能力高低等同未來績效。
- 模型已預測真實持股、股數或成本。
- 模型可預測未來股價、買賣點或報酬率。
- 社群整體多空比例代表該使用者的個人情緒。
- Synthetic profiles 是真實會員研究結果。

### 4.3 Risk 與 Recommendation 定義

本 MVP 可提供的是**歷史曝險解釋**，不是個人理財適合度測驗：

| 可提供 | 不提供 |
|---|---|
| 歷史波動與回落情境 | 心理風險承受度診斷 |
| 產業／標的集中程度 | 特定股票推薦 |
| 進場月份的 regime 與 anomaly | 買進、賣出、加碼、減碼指令 |
| 與大盤或同類情境的回顧 | 目標價與未來報酬預測 |
| 建議回看哪些證據 | 保證獲利或績效排名 |

## 5. ML Training 規格

### 5.1 訓練任務

第一版只實作兩個沒有個人 label 依賴的模型：

#### Model A：Market Regime Clustering

- 演算法候選：KMeans、Gaussian Mixture Model。
- Sample unit：`stock_id + YYYY-MM`。
- 目的：將每個股票月份分到可解釋的歷史市場情境。
- 產出：`regime_id`、`regime_label`、`distance/confidence`、`model_version`。
- Cluster 名稱由團隊檢視 centroid 後固定，不允許 LLM 改寫 assignment。

#### Model B：Market Anomaly Detection

- 演算法：IsolationForest baseline。
- Sample unit：`stock_id + YYYY-MM`。
- 目的：辨識相對自身歷史與市場分布顯著的月份。
- 產出：`anomaly_level`、`anomaly_score`、`evidence_feature_keys`、`model_version`。
- UI 只顯示「一般／注意／顯著」與具體證據，不以原始分數製造精確錯覺。

### 5.2 共用 Feature Contract

沿用 `packages/mindfolio-core/src/mindfolio_core/features/__init__.py`：

```text
feature_version = monthly-features-v1

monthly_return
volatility
max_drawdown
volume_change
turnover
institutional_net
community_heat
community_bullish_ratio
```

必要規則：

- Training 與 serving 必須 import 同一份 feature keys 與 normalization contract。
- 缺值策略、日期截點、單位與 winsorization 參數必須寫入 artifact metadata。
- 不可在 API 內複製一份不同公式，避免 training-serving skew。
- 所有特徵只使用目標月份當下或之前可取得的資料，避免 future leakage。

### 5.3 Artifact Contract

```json
{
  "model_name": "market-regime-kmeans",
  "model_version": "2025-v1",
  "feature_version": "monthly-features-v1",
  "training_range": ["2025-01-01", "2025-12-31"],
  "sample_count": 0,
  "feature_keys": [],
  "preprocessing": {
    "missing_values": "documented-policy",
    "scaler": "StandardScaler"
  },
  "metrics": {
    "silhouette": null,
    "stability": null
  },
  "generated_at": "ISO-8601",
  "artifact_sha256": "..."
}
```

沒有實際訓練前，`sample_count`、metrics 與版本不可填入虛構成績。

### 5.4 評估方式

| 模型 | 離線評估 | 人工驗證 |
|---|---|---|
| Regime | silhouette、cluster stability、cluster size distribution | centroid 是否可解釋、不同 cluster 是否實質分離 |
| Anomaly | time-split stability、score distribution | 抽樣月份的證據 precision review |

無監督模型不使用 Accuracy，也不宣稱「人格辨識準確率」。

## 6. Online Inference 規格

### 6.1 部署方式

不新增獨立 ML service。FastAPI 啟動時由既有 process 載入核准 artifact：

```text
apps/ai-training（offline）
        ↓ publish artifact
本機 volume / S3 versioned object
        ↓ startup load
apps/api MarketContextService（online inference）
```

這可維持現有 Docker Compose 與 EC2 部署拓撲，減少網路 hop、服務發現與額外故障點。

### 6.2 Service Contract

```text
MarketContextService.predict(stock_id, month)
  → MarketContextEvidence
```

建議 DTO：

```json
{
  "stock_id": "2330",
  "month": "2025-04",
  "regime_id": 2,
  "regime_label": "高波動反彈",
  "regime_confidence": 0.81,
  "anomaly_level": "attention",
  "evidence": [
    {"key": "volatility", "label": "月波動", "value": 0.18},
    {"key": "institutional_net", "label": "法人淨買賣", "value": -28000}
  ],
  "feature_version": "monthly-features-v1",
  "model_version": "2025-v1",
  "source_as_of": "2025-12-31"
}
```

### 6.3 Fallback

- Artifact 缺少、checksum 錯誤或 feature version 不符：API 啟動可繼續，但標記 inference unavailable。
- 單筆股票月份無 feature：只略過該筆 market context，不得讓 reconstruction 失敗。
- ML 不可改寫 `ReconstructionResult` 的交易結果、人格、分數或 holding candidates。
- 完整報告仍可使用 deterministic context 生成 fallback template。

## 7. 完整 AI 投資報告

### 7.1 生成時機

- 報告必須已被目前 session 會員 claim。
- 使用者第一次開啟完整報告時才生成，避免匿名流量產生不必要的 Bedrock 成本。
- 相同 `report_id + context_version + prompt_version + model_version` 必須重用既有結果。
- 重新生成只在 context 或 prompt/model version 改變時發生。

### 7.2 LLM Input

LLM 不讀原始 CSV、不連資料庫自行查詢，也不自行計算。輸入只使用 server 組好的 `InvestmentAIContext`：

```json
{
  "report_id": "opaque-id",
  "reconstruction": {
    "persona_code": "...",
    "persona_name": "...",
    "average_return": 12.3,
    "confidence": 84,
    "scores": {},
    "trades": []
  },
  "market_contexts": [],
  "confirmed_holding_ids": ["2330"],
  "data_quality": {
    "exact_price_count": 2,
    "band_price_count": 3,
    "missing_market_context_count": 0
  },
  "versions": {
    "context": "investment-ai-context-v1",
    "feature": "monthly-features-v1",
    "model": "2025-v1",
    "prompt": "investment-report-v1"
  }
}
```

### 7.3 LLM Output

LLM 先輸出通過 Pydantic 驗證的 JSON，再由 API 組成 Markdown；不可直接信任任意 HTML。

```json
{
  "title": "你的 2025 Investment DNA",
  "executive_summary": "...",
  "strengths": ["..."],
  "watchouts": ["..."],
  "market_context_summary": "...",
  "evidence_refs": ["trade:2330:2025-04", "model:regime:2025-v1"],
  "suggested_questions": ["...", "...", "..."]
}
```

API response 可另附 server-rendered `markdown`，Web 僅允許安全 Markdown subset，不使用 unsanitized `dangerouslySetInnerHTML`。

### 7.4 報告章節

1. 核心 Investment DNA。
2. 2025 歷史交易重建摘要。
3. 可驗證的優勢。
4. 需要留意的行為或曝險特徵。
5. 買進月份的市場 regime 與異常證據。
6. 資料限制與信心說明。
7. 三個下一步建議問題。

## 8. Context-aware AI 問答

### 8.1 互動定位

問答不是首頁 ChatGPT，也不要求使用者維持長對話。第一版以低門檻按鈕為主：

```text
[為什麼我是這種 Investment DNA？]
[哪一筆交易最影響結果？]
[為什麼這個月份被標成異常？]
```

使用者可選填一個自由問題，但每個 request 視為單輪問答。MVP 不做 agent、tool planning、vector memory 或長期聊天記憶。

### 8.2 問答 Context

每次由 server 重新載入：

- 已 claim 報告的 `ReconstructionResult`。
- 原始 trades 經後端再次驗證後的必要摘要。
- MarketContextEvidence。
- confirmed holdings 關係。
- 完整 AI report 的結構化 sections。
- 問題文字。

不得讓 client 自行傳入 persona、報酬、持股或模型結論作為可信 context。

### 8.3 Answer Contract

```json
{
  "answer": "...",
  "evidence_refs": ["trade:2330:2025-04"],
  "limitations": ["此分析使用 2025 封存資料，不代表目前行情"],
  "source": "bedrock",
  "prompt_version": "report-qa-v1"
}
```

Bedrock 失敗或輸出不合法時，建議問題回傳 deterministic evidence answer；自由問題回傳可重試狀態，不生成無依據內容。

## 9. API 增量契約

Base path 維持 `/api/v2`。

### 9.1 取得／生成完整報告

```http
POST /reports/{report_id}/ai-report
Authorization: Bearer <session-token>
```

規則：

- 只能存取 `claimed_by == current_member` 的報告。
- 有相同版本 cache 時直接回傳。
- 404：claimed report 不存在。
- 422：context 無法通過驗證。
- 503：AI provider 與 fallback 都不可用。

### 9.2 報告問答

```http
POST /reports/{report_id}/questions
Authorization: Bearer <session-token>
```

Request：

```json
{
  "question_id": "why-persona",
  "question": null
}
```

`question_id` 與自由 `question` 二擇一；自由問題建議限制 300 字，並做 rate limit。

### 9.3 Dashboard 增量

`GET /me/dashboard` 的 `report` 新增 optional summary，不阻擋舊 client：

```json
{
  "ai_report_status": "not_generated|ready|fallback|unavailable",
  "ai_report_version": "investment-report-v1",
  "suggested_questions": []
}
```

## 10. Persistence 最小變更

不新增 chat/message table。MVP 僅擴充現有 `reconstruction_reports`：

```sql
ALTER TABLE reconstruction_reports
  ADD COLUMN IF NOT EXISTS ai_context JSONB,
  ADD COLUMN IF NOT EXISTS ai_report JSONB,
  ADD COLUMN IF NOT EXISTS ai_report_version TEXT,
  ADD COLUMN IF NOT EXISTS ai_report_generated_at TIMESTAMPTZ;
```

問答曝光、點擊、成功、fallback 與 helpful feedback 沿用 `interaction_events`：

```text
ai_report_open
ai_report_generated
ai_question_chip_click
ai_question_submitted
ai_answer_rendered
ai_answer_fallback
ai_answer_helpful
```

事件 metadata 只存 `report_id` 的不可逆 hash、question_id、source、latency bucket 與版本，不存完整自由問題或完整回答，降低個資與敏感財務內容風險。

## 11. 模組最小改動清單

### 11.1 `packages/mindfolio-core`

- 完成 `monthly-features-v1` feature builder。
- 新增 inference DTO／Protocol，不依賴 FastAPI 或 Bedrock。
- 保持 reconstruction 與 persona mapping 不變。

### 11.2 `apps/ai-training`

- 新增 feature table build、regime/anomaly train、evaluate、publish scripts。
- 產出 versioned artifact、metadata、evaluation report。
- 不啟動常駐 HTTP service。

### 11.3 `apps/api`

- 新增 `MarketContextService`，在 startup 載入 artifact。
- 新增完整 report schema、prompt、fallback、guardrail。
- 在既有 retention router 增加兩個 report-scoped endpoint。
- 在既有 repository 擴充 AI report cache 讀寫。
- 沿用 session identity 與 report ownership gate。

### 11.4 `apps/web`

- `/result` 增加完整報告 teaser，不增加聊天入口。
- `/app` 增加 `InvestmentAIReport` 區塊。
- 增加三個 suggested question chips 與選填文字問題。
- typed client 增加 schema；所有金融值仍只讀 API response。

### 11.5 `infra/schema`

- 只對既有 `reconstruction_reports` 加 nullable AI cache 欄位。
- 不新增獨立 vector DB、feature store、message DB 或 queue。

## 12. Guardrails 與安全性

### 12.1 金融內容

- 禁止買進、賣出、加碼、減碼與目標價。
- 禁止保證獲利或以歷史結果承諾未來績效。
- 禁止把 Investment DNA 描述成心理診斷。
- 每個結論至少對應一個 evidence ref；無證據就明確回答資料不足。
- 必須標示資料截點 `2025-12-31`。

### 12.2 應用安全

- 報告與問答 endpoint 必須使用 `require_member`。
- 後端依 session 推導 member，不接受 client `user_id`。
- 對自由問題做長度限制、rate limit 與 prompt-injection delimiter。
- LLM output 必須通過 Pydantic schema、禁語掃描與 evidence ref 驗證。
- Markdown 僅允許標題、段落、清單與強調；禁止 HTML、script、iframe、外部圖片。
- Log 不記錄 claim token、完整持股輸入、完整問題與回答。

## 13. 可觀測性與成本

每次生成記錄：

- `source=bedrock|fallback`。
- `prompt_version`、`model_version`、`feature_version`。
- latency bucket、input/output token bucket。
- guardrail failure reason code。
- cache hit/miss。

成本控制：

- 完整報告只在 claim 後 lazy generate。
- 相同版本只生成一次。
- 建議問題優先使用小型 context；不把原始 CSV 傳給 LLM。
- 每位會員／報告限制問答頻率與每日上限。

## 14. KPI

### 14.1 產品 KPI

| Funnel | 指標 |
|---|---|
| Acquisition | Time Machine completion rate |
| Activation | report claim rate、confirmed holding activation rate |
| AI value | full report unlock rate、suggested question CTR |
| Quality | answer helpful rate、fallback rate、evidence open rate |
| Retention | 7-day Portfolio Radar return rate |

### 14.2 技術 KPI

- Artifact load success rate。
- Training/serving feature version mismatch count。
- AI report cache hit rate。
- Bedrock success/fallback rate。
- P95 report generation latency、P95 question latency。
- Guardrail rejection rate。
- Evidence ref validation failure rate。

KPI 必須標示為「目標」或「實測」，不可在 Demo 前把預期數字寫成既有成果。

## 15. 驗收條件

### 15.1 ML

- [ ] 可由官方 CSV 重建 `monthly-features-v1` stock-month table。
- [ ] Regime 與 anomaly 模型可重複訓練並產出 metadata、checksum 與真實 metrics。
- [ ] FastAPI 使用與 training 相同的 feature contract。
- [ ] Artifact 遺失或版本不符時 reconstruction 仍可完成。
- [ ] ML output 不改寫金融結果、人格或 confirmed holdings。

### 15.2 AI Report

- [ ] 未 claim 報告不可取得完整 AI report。
- [ ] 已 claim 報告可產生一次並在相同版本下重用 cache。
- [ ] 每項 watchout 與 market context 都有 evidence ref。
- [ ] Bedrock 失敗時回傳 deterministic fallback report。
- [ ] Web 安全呈現 Markdown，不執行 LLM 產生的 HTML。

### 15.3 AI Q&A

- [ ] 使用者可用三個預設按鈕取得個人化回答。
- [ ] 自由問題為選填，且不影響主流程完成。
- [ ] API 只接受已 claim 且屬於目前會員的 report。
- [ ] 回答不得出現買賣指令、目標價、獲利保證或心理診斷。
- [ ] 無足夠資料時明確回答限制，不補造數字。
- [ ] 互動事件可送入既有 `/events/batch`。

### 15.4 Regression

- [ ] 現有五檔 reconstruction、報告認領、confirmed holdings 與 dashboard contract 維持相容。
- [ ] Bedrock、ML artifact 或 PostgreSQL 任一非核心依賴失效時，匿名 Time Machine 仍可完成。
- [ ] Python tests 與 React production build 通過。
- [ ] Docker Compose 仍維持 web + api + postgres，無新增常駐服務。

## 16. 三天實作切割

### Day 1：資料與模型

- 完成 stock-month feature table。
- 訓練 regime baseline 與 anomaly baseline。
- 產出 artifact、metadata 與 evaluation report。
- 完成 `MarketContextService` artifact load 與 fallback tests。

### Day 2：完整報告

- 完成 `InvestmentAIContext` builder。
- 完成 report schema、Bedrock prompt、guardrail 與 deterministic fallback。
- 完成 report endpoint、cache persistence 與 Web 報告區塊。

### Day 3：低門檻問答與驗收

- 完成三個 suggested question templates 與單輪問答 endpoint。
- 完成 Web question chips、事件追蹤與錯誤狀態。
- 執行 regression、Docker Compose、Demo 與簡報證據整理。

### Cut line

若時間不足，依序砍除：

1. 自由文字問題，保留三個 evidence-based 問題。
2. GMM candidate，只保留 KMeans baseline。
3. 動態 Markdown 樣式，保留結構化 report cards。

不可砍除：deterministic fallback、report ownership、evidence refs、guardrails、artifact versioning。

## 17. 架構選擇的優缺點

| 選擇 | 優點 | 缺點／代價 |
|---|---|---|
| ML 內嵌 FastAPI inference | 不新增服務、低延遲、三天可完成 | API image 會包含 scikit-learn runtime；artifact 更新需嚴格版本控管 |
| LLM 僅解釋 verified context | 可追溯、降低幻覺、容易 fallback | 自由度較低，報告品質依賴 context builder 完整度 |
| 報告 claim 後 lazy generate | 降低成本並強化註冊價值 | 首次開啟有生成延遲，需要 loading UX |
| 單輪問答、不做長期 chat | 低門檻、低儲存風險、符合現有使用行為 | 無法處理長篇追問；未來需要 conversation summary 才能擴充 |
| 不做個人 ML persona | 不虛構 label、人格結果穩定可重算 | AI training 的主角是市場情境，而非個人分類；Pitch 必須清楚說明分工 |

## 18. 明確不採用

- 不導入 Go backend 或拆出 Python ML HTTP service。
- 不導入 LangGraph、CrewAI、OpenClaw、Hermes 或 multi-agent framework。
- 不導入 RAG、向量資料庫或 knowledge graph。
- 不用 synthetic users 宣稱真實投資人格 discovery。
- 不以 KMeans cluster 取代現有 deterministic persona。
- 不讓 LLM 讀 raw CSV、計算報酬或決定持股候選。
- 不把問答改成 acquisition 入口。

## 19. Pitch 技術說法

> Mindfolio 不讓語言模型替使用者算分，也不以缺乏標籤的資料假裝預測投資能力。既有重建引擎先以 2025 封存行情產生可重算的 Investment DNA；離線 ML 再從官方價格、法人與社群資料辨識每筆交易所處的市場 regime 與異常情境；最後 Bedrock 只將這些已驗證事實整理成個人化報告與證據型問答。這讓數學、ML 與 LLM 各自負責最適合的工作，在不增加輸入摩擦與不重做架構的前提下，讓 AI 從通用文案升級為真正理解使用者歷史投資情境的產品能力。
