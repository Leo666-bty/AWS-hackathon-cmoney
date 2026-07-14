# Mindfolio AI — Team MVP Spec

> 本文件是兩人團隊的唯一實作基準。其他文件若衝突，以本文件為準。

## 1. Product

### Name

Mindfolio AI

### Concept

**Reverse Portfolio Onboarding**：在籌碼 K 線既有頁面先呈現有證據的市場洞察，再用一次點擊確認使用者與股票的關係。

### Promise

> Zero Prompt、Zero Upload、One Tap。

### Why now

CMoney 已觀察到 WebUI ChatGPT 使用率低。使用者不想先想問題再與 AI 長聊；同樣地，也不會願意先上傳券商資料或填完整資產，才換取未知價值。

## 2. Scope

### Must have

- 2382 廣達個股頁
- 2025-12-31 市場、法人、社群 evidence
- 背離洞察卡
- `是我的持股／只是觀察／不相關`
- 持股確認後 Portfolio 更新
- 已確認持股的今日優先事件
- 資料與投資建議免責聲明

### Must not have

- Chat UI
- Screenshot upload
- 自由文字輸入
- 精確股數、成本、券商或總資產
- 個人焦慮分數
- 持股預測模型與準確率
- Multi-agent、RAG、Vector DB

## 3. Persona & Scenario

LEO 是籌碼 K 線使用者，會查看廣達籌碼，但尚未在 CMoney 建立任何已確認持股。LEO 不願聊天，也不願揭露完整財務資料。

## 4. Core Flow

```text
LEO 打開 2382 個股頁
→ 系統顯示法人與社群背離洞察
→ LEO 看完證據
→ 選擇股票關係
→ API 保存使用者明確回饋
→ Portfolio Context 更新
→ 同一事件以持股優先級呈現
```

## 5. UX States

### S0 — Discovery

- 顯示市場 evidence。
- 不使用「你的持股」語氣。
- 提供三個按鈕。

### S1 — Confirmed Holding

- relationship = `holding`
- 顯示「廣達已加入你的庫存情境」。
- Portfolio count 由 0 變 1。

### S2 — Watch Only

- relationship = `watch_only`
- 保留一般資訊，不建立持股。

### S3 — Irrelevant

- relationship = `irrelevant`
- 降低相似卡片優先級。

## 6. Evidence Contract

| Field | Value |
|---|---|
| as_of | 2025-12-31 |
| stock | 2382 廣達 |
| close | 272 |
| annual_return | −0.7% |
| institutional_net_20d | −60,265 張 |
| community_bullish_ratio_7d | 93.9% |
| community scope | 明確表態看多或看空的貼文 |

所有數字必須從程式計算或固定 validated JSON 取得，不能由 LLM 自行推導。

## 7. Moment Engine

三天版本使用可解釋 scoring：

```text
priority = relevance × impact × novelty − interruption_cost
```

- `relevance`：目前正在查看該股票；若已確認持有則更高。
- `impact`：法人、價格或社群變化強度。
- `novelty`：相較近期是否是新事件。
- `interruption_cost`：同日已顯示卡片、曾選不相關等。

Demo 只有一張廣達卡，不做推薦系統訓練。

## 8. Generative Action Card

AI 必須回傳結構化 JSON，而不是聊天文字：

```json
{
  "card_type": "signal_divergence",
  "stock_id": "2382",
  "title": "市場很樂觀，法人卻仍在調節",
  "summary": "兩種訊號方向不一致",
  "evidence": [
    "近20日法人賣超60265張",
    "明確多空貼文中93.9%偏多"
  ],
  "actions": [
    {"id":"confirmed_holding","label":"是我的持股"},
    {"id":"watch_only","label":"只是觀察"},
    {"id":"irrelevant","label":"不相關"}
  ]
}
```

## 9. Architecture

```text
apps/web
  → apps/api
      → CMoney CSV adapter
      → Context Builder
      → Moment Engine
      → Amazon Bedrock
      → PostgreSQL schema
```

### Web

React + Vite。Day 1 可先以 `apps/web/prototype` 驗證互動。

### API

FastAPI。API contract 位於 `apps/api/contracts/openapi.yaml`。

### Database

PostgreSQL。Schema 位於 `infra/schema/001_init.sql`。

## 10. Data Ownership

| 資料 | 來源 | 可宣稱 |
|---|---|---|
| 市場／法人／社群 | 官方 CSV | 股票情境與彙總趨勢 |
| 是否持有 | LEO 一鍵確認 | 使用者已確認持股 |
| 目前頁面 | Demo Web event | 當下 context |
| 成本／股數 | 未收集 | 不知道、不可推測 |

## 11. Guardrails

- 候選或未確認關係不可寫入持股。
- 不把社群資料描述為使用者心理。
- 不產生買賣方向、目標價與報酬保證。
- 卡片顯示資料日期。
- Bedrock 失敗時回傳固定模板。

## 12. Acceptance Criteria

- [ ] Prototype 初始 Portfolio 為 0。
- [ ] 個股頁在沒有聊天與上傳的情況下顯示廣達卡。
- [ ] 點「是我的持股」後 Portfolio count 變 1。
- [ ] Portfolio 頁顯示 2382 與背離事件。
- [ ] 「只是觀察／不相關」都不建立持股。
- [ ] Reset 可重跑 Demo。
- [ ] 所有日期與數字符合 evidence contract。
- [ ] 手機寬度仍可完成操作。

## 13. KPI

North Star：至少完成一檔使用者確認持股的人數。

Secondary：卡片一鍵回饋率、確認後洞察查看率、D7 回訪、30 日狀態更新率。

## 14. Three-Day Definition of Done

- Web、API contract、schema、資料計算與 Bedrock fallback 齊全。
- Live Demo 與備援影片可完整展示一次閉環。
- GitHub README、HTML/PDF 簡報與繳交連結完成。
- 不以未驗證 KPI、虛構持股準確率或個人焦慮作為成果。
