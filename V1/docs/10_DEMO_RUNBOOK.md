# Demo Runbook

## Goal

120 秒證明：不用聊天、不用上傳、不用填表，LEO 在原本的籌碼 K 線研究流程中即可建立第一檔已確認持股，並留下可衡量的即時互動資料。

## Setup

- Persona：LEO
- 日期：2025-12-31
- 股票：2382 廣達
- Portfolio：0 檔
- 從 `apps/web/prototype/index.html` 的自選股頁開始

## Script

### 1. Existing Workflow（15 sec）

「LEO 不會打開另一個 AI Chat。他照常從自選股打開廣達。」點擊 2382。

### 2. Evidence, Not Guessing（25 sec）

依序切換盤後、社群、新聞。指出：近 20 日法人 −60,265 張；近 7 日明確多空貼文 93.9% 偏多。新聞目前清楚標示為 Demo Feed。

### 3. Reverse Onboarding（20 sec）

展開完整證據，點「是我的持股」。說明 LEO 沒有輸入 Prompt、股數、成本或券商資料。

### 4. Contextual AI, Not ChatGPT Page（20 sec）

點「為什麼會背離？」展示單一情境 follow-up。接著點「有點擔心」，說明這是 LEO 明確回覆的 Concern Signal，不是模型診斷。

### 5. Personal Value（20 sec）

開「我的庫存」，展示廣達已加入、背離事件成為今日優先項目，而且系統明示不知道成本與股數。

### 6. Measurable Loop（20 sec）

開「營運 Dashboard」，展示 `stock_open`、`news_open`、`relationship_feedback`、`concern_feedback` 等事件與 local outbox 狀態。

## Closing Line

「傳統 AI 等使用者想問題；Mindfolio 在值得注意的時刻先給證據，再用一次點擊建立持股情境與提醒偏好。」

## Backup

- Bedrock 失敗：固定敘事與 follow-up。
- API 失敗：事件保留 local outbox，清楚顯示 queued。
- 網路失敗：直接開本機 reference 或播放錄影。

## Forbidden Claims

- AI 已準確猜出 LEO 的持股。
- 93.9% 的使用者看多，或 LEO 的焦慮是 93.9%。
- Demo Feed 是官方新聞資料。
- AI 建議買進或賣出廣達。
