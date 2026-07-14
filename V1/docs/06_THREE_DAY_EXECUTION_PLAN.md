# Three-Day Execution Plan

## Team

兩人、約 48 人時。A 負責 Web／Demo／Pitch，B 負責 Data／API／Bedrock／DB；每天兩次一起驗收閉環。

## Day 1 — Data, DB, and the Non-AI Closed Loop

### A：Web

- 建 React shell：自選股、個股四分頁、我的庫存。
- 完成情境卡、三個關係回饋、Concern Signal。
- 建 event collector 與 local outbox。

### B：Backend

- 驗證 2382 官方數字並輸出 evidence JSON。
- 建 PostgreSQL schema 與 seed。
- 實作 context、feedback、portfolio、events/batch happy path。

### Day 1 Gate

不用 Bedrock也能：開股票 → 看證據 → 確認持股 → DB 保存 → Portfolio 更新 → Dashboard 查到事件。

## Day 2 — AI Narrative, News Slice, and Metrics

### A：Web

- 串 API 與 queued/synced UI。
- 完成情境式 follow-up、新聞 Demo Feed、營運 Dashboard。
- 基本手機版與錯誤狀態。

### B：Backend

- CSV adapter、Context Builder、Moment rule。
- 跑 `apps/ai-training` 離線 Market Moment Detector，輸出 MomentSignal；若品質或時間不過 Gate，立即改用 validated rules。
- Bedrock 結構化輸出與固定模板 fallback。
- Concern feedback、metrics aggregation、最近事件。

### Day 2 Gate

可從頭操作兩次；所有事件有時間戳、可持久化，數字與 2025-12-31 evidence 一致；模型輸出或 rules fallback 皆能產生同一份 MomentSignal contract。

## Day 3 — Deploy and Freeze

- 上午：整合、部署、修 happy path。
- 12:00：功能凍結，不再加新模組。
- 下午：Pitch HTML/PDF、README、Demo 影片、備援錄影。
- 最後：無痕瀏覽器重跑、斷 API 測 outbox、檢查所有繳交連結。

## Scope Cuts

依序砍除：真推播、多檔股票、自由聊天、新聞真實串接、Bedrock 動態文案。不可砍：一鍵回饋、事件寫入、Portfolio 更新、官方 evidence、Concern Signal、最小 Dashboard。

## Non-goals

不做持股預測、焦慮診斷、漲跌預測、RAG、向量資料庫、Agent framework、完整 Auth/RBAC、完整測試矩陣。AI training 只限離線 Market Moment Detector；其餘只做 happy path、必要錯誤提示與可重跑 Demo。
