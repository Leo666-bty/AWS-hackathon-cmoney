# Mindfolio AI — Team MVP Spec

> 兩人三天實作的唯一基準。其他文件若衝突，以本文件為準。

## 1. Product Definition

**Reverse Portfolio Onboarding**：在籌碼 K 線既有頁面先呈現有證據的市場洞察，再用一次點擊確認使用者與股票的關係。

Promise：**Zero Prompt、Zero Upload、One Tap first.**

CMoney 已觀察到 ChatGPT 式 WebUI 使用率低。問題不只是回答品質，而是使用者不會主動想問題、長聊、上傳券商截圖或先填完整資產。Mindfolio 在值得注意的市場時刻先提供價值，再收最低敏感度的明確回饋。

## 2. Three-Day MVP Scope

### Must Have

- 以 LEO 為 Persona，從自選股進入 2382 廣達。
- 個股頁包含即時、盤後、社群、新聞四個可操作分頁。
- 2025-12-31 市場、法人、社群 evidence。
- 一張「法人 × 社群背離」AI 情境卡。
- `是我的持股／只是觀察／不相關`。
- 三個 contextual follow-up，不需輸入 Prompt。
- `有點擔心／例行查看／不用提醒` Concern Signal。
- 我的庫存顯示已確認持股與今日優先事件。
- 前台事件 collector、local outbox、API batch contract。
- 內部 Dashboard 顯示最小漏斗與最近事件。
- React、FastAPI、PostgreSQL happy path 與離線 reference。

### Explicit Non-goals

- 獨立 ChatGPT 首頁、自由長對話。
- Screenshot upload。
- 首次互動收精確股數、成本、券商或總資產。
- 個人焦慮分數、心理診斷。
- 持股預測準確率、股價預測、買賣建議。
- 焦慮診斷模型；Concern Signal 僅來自使用者明確回覆。
- Multi-agent、RAG、Vector DB、完整通知服務。
- 完整 Auth/RBAC、完整測試矩陣與多股票產品化。

## 3. Persona and Scenario

LEO 平常用籌碼 K 線研究股票，但沒有在 CMoney 建立庫存。他不願為了 AI 先聊天或提供敏感資料。LEO 從自選股打開廣達，看完法人、社群與新聞後，AI 主動整理背離；LEO 只需一鍵確認關係與提醒需求。

## 4. Page Map

| Page | User Value | Required State |
|---|---|---|
| Watchlist | 延續籌碼 K 線入口 | stocks、as_of |
| Stock | 研究證據與取得 AI 洞察 | StockContext、ActionCard |
| Portfolio | 查看已確認關係與個人化優先事件 | PortfolioRelationship、ConcernFeedback |
| Dashboard | 驗證互動資料真的產生 | InteractionEvent、metrics |

Dashboard 是內部驗證面，不和前台資訊混在同一頁。

## 5. Core Flow

```text
watchlist_view
→ stock_open(2382)
→ stock_tab_view(aftermarket/community/news)
→ card_impression
→ card_evidence_open
→ relationship_feedback
→ ai_followup_open (optional)
→ concern_feedback (optional)
→ portfolio_view
→ dashboard verifies the event trail
```

## 6. UX States

### Discovery

- 不使用「你的持股」語氣。
- 顯示背離摘要、資料日期與 evidence。
- 看證據後才出現三個關係按鈕。

### Confirmed Holding

- `relationship=holding`。
- Portfolio count 由 0 變 1。
- 廣達重大事件提高優先級。
- 明示未知股數、成本與券商。

### Watch Only / Irrelevant

- `watch_only` 保留一般資訊，不使用持股語氣。
- `irrelevant` 降低同類卡片優先度。
- 兩者都不建立持股。

### Concern Signal

- `worried`：後續優先整理證據，不強化恐懼。
- `routine`：維持一般頻率。
- `mute`：降低提醒。

這是使用者回覆，不是模型診斷。

## 7. Evidence Contract

| Field | Value |
|---|---|
| as_of | 2025-12-31 |
| stock | 2382 廣達 |
| close | 272 |
| annual_return | −0.7% |
| institutional_net_1d | +3,957 張 |
| institutional_net_20d | −60,265 張 |
| institutional_holding_ratio | 32.91% |
| dividend_yield | 4.78% |
| community_bullish_7d | 216 |
| community_bearish_7d | 14 |
| community_bullish_ratio_7d | 93.9% |

93.9% 的分母是明確表態看多或看空的貼文，不能描述成 LEO 的情緒。

## 8. News Contract

官方 package 沒有新聞。MVP reference 可使用 `demo_news`，但 UI、API 與 DB 都要標示 `MVP Demo Feed` / `is_demo=true`。正式上線前改接有授權 CMoney 新聞來源。`news_open` 可作為頁面 context，但不能推論持股。

## 9. AI Responsibilities

### Deterministic Layer

- 計算法人、社群與價格 evidence。
- 以 `relevance × impact × novelty − interruption_cost` 排序時刻。
- 產生可追溯 Context JSON。
- 聚合事件與漏斗指標。

### Bedrock Layer

- 將 evidence 改寫成簡潔 Action Card。
- 根據已確認 relationship 切換語氣。
- 回答三個 suggested follow-up。
- 通過 schema 與禁詞檢查；失敗使用固定模板。

### Training Position

三天不訓練持股或焦慮模型，因為沒有 Ground Truth。`apps/ai-training` 只訓練無監督 Market Moment Detector，使用官方每日資料找出值得呈現的異常與背離時點。

模型輸出 `MomentSignal`，包含 `moment_type`、`anomaly_score`、`severity`、`evidence` 與 `model_version`。API 再結合使用者已確認 relationship 與 interruption cost 決定卡片排序。UI 不直接顯示 anomaly score，避免被誤認為預測準確率。

MVP 收集的 `relationship_feedback`、`concern_feedback` 與卡片互動，未來可訓練「何時顯示哪張卡」的 ranking model；不能宣稱已學會真實庫存。

## 10. Interaction Event Contract

Required fields：

```json
{
  "event_id": "uuid",
  "session_id": "uuid-or-string",
  "event_type": "relationship_feedback",
  "user_id": "LEO",
  "stock_id": "2382",
  "card_id": "signal-divergence-2382",
  "surface": "stock_insight",
  "action": "confirmed_holding",
  "occurred_at": "ISO-8601",
  "source_date": "2025-12-31",
  "metadata": { "time_to_action_ms": 3200 }
}
```

Event types：`watchlist_view`、`stock_open`、`stock_tab_view`、`card_impression`、`card_evidence_open`、`relationship_feedback`、`concern_feedback`、`ai_followup_open`、`portfolio_view`、`holding_removed`、`news_open`、`dashboard_view`。

前端先寫 event history 與 outbox。只有 `/v1/events/batch` 接受後才從 `queued` 變成 `synced`；不得模擬成功。

## 11. Architecture

```text
React
  → FastAPI
      → CSV Adapter / Context Builder / Moment Engine
      → Bedrock + fixed-template fallback
      → Portfolio / Concern / Event services
  → PostgreSQL

CMoney CSV
  → apps/ai-training（offline）
  → MomentSignal JSONL
  → FastAPI Moment Engine
```

OpenAPI：`apps/api/contracts/openapi.yaml`

Schema：`infra/schema/001_init.sql`

Interactive reference：`apps/web/prototype/`
AI training：`apps/ai-training/`

## 12. API Minimum

- `GET /v1/stocks/{stock_id}/context`
- `GET /v1/users/{user_id}/cards/next`
- `POST /v1/users/{user_id}/cards/{card_id}/feedback`
- `POST /v1/users/{user_id}/concern-feedback`
- `GET /v1/users/{user_id}/portfolio`
- `POST /v1/events/batch`
- `GET /v1/users/{user_id}/events`
- `GET /v1/dashboard/metrics`

## 13. Database Minimum

users、stocks、portfolio_relationships、action_cards、card_feedback、concern_feedback、interaction_events、demo_news。

`average_cost` 與 `shares` 可為 null；首次流程不詢問。三天只需 happy path 與 `event_id` idempotency，不做正式產品級稽核系統。

## 14. Guardrails

- 未確認 relationship 不得寫入持股。
- 社群彙總不得描述為個人心理。
- 不產生買賣方向、目標價、報酬保證。
- 所有數字由程式計算並保留 source date。
- Demo News 必須有清楚標籤。
- API 失敗時事件留在 outbox，UI 明示待同步。
- LLM 回覆不符合 schema 時使用固定模板。

## 15. Metrics

North Star：至少完成一檔使用者確認持股的人數。

MVP Dashboard：事件數、卡片曝光、關係回饋、已確認持股、最近事件與同步狀態。

Demo 數字只證明 event pipeline 工作，不代表市場成效。真正 A/B Test 比較「先問持股」與「先給洞察」的回饋率、持股確認率、不相關率與 time-to-action。

## 16. Acceptance Criteria

- [ ] 初始頁是自選股，Portfolio 為 0。
- [ ] 點 2382 後進入獨立個股頁。
- [ ] 即時、盤後、社群、新聞分頁可切換並產生事件。
- [ ] 社群頁明示不是 LEO 個人情緒。
- [ ] 新聞頁明示 Demo Feed。
- [ ] 看證據後可一鍵回覆 relationship。
- [ ] `holding` 使 Portfolio count 變 1；另外兩種不建立持股。
- [ ] Suggested follow-up 可顯示 context-aware 回覆。
- [ ] Concern Signal 可保存並反映在 Portfolio。
- [ ] Dashboard 與前台分頁獨立，能看到事件與 queued/synced。
- [ ] 重新整理仍保留 demo state 與 outbox。
- [ ] API 不可用時不顯示假成功。
- [ ] Reset 只清除 Mindfolio demo keys。
- [ ] 手機寬度仍可完成主閉環。
- [ ] MomentSignal example 符合 JSON schema，且 UI 不顯示模型內部分數。

## 17. Definition of Done

- React、FastAPI、PostgreSQL happy path 可部署。
- AI training 可輸出 MomentSignal；訓練失敗時固定 evidence 仍可完成 Demo。
- Bedrock 可用時動態生成，不可用時固定模板完整運作。
- Live Demo 與離線 reference 都可跑完整閉環。
- README、HTML/PDF deck、Demo 影片與六項繳交連結完成。
- 不以虛構持股準確率、焦慮分數或單一 LEO session KPI 當成果。
