# Three-Day Execution Plan

## 團隊

兩人：A 負責 Web／Demo／Pitch，B 負責資料／API／Bedrock。共同維護 Spec 與驗收。

## Day 1：先跑通沒有 AI 的閉環

### A
- 建立個股頁、洞察卡與 Portfolio 頁
- 完成三個一鍵回饋狀態

### B
- 驗證 2382 官方資料
- 完成 evidence JSON 與 OpenAPI
- 建立 schema 與固定資料 API

### Gate

不用 Bedrock，也能從洞察卡點到 Portfolio 更新。

## Day 2：接資料與 Bedrock

### A
- React 串 API
- 完成 loading、錯誤與 fallback
- 手機版基本適配

### B
- CSV adapter 與計算函式
- Moment ranking
- Bedrock 結構化卡片輸出與 guardrails

### Gate

Live Demo 可以完整跑兩次，數字與 2025-12-31 一致。

## Day 3：凍結、部署、報告

- 上午：整合與部署
- 中午前：功能凍結
- 下午：HTML/PDF 簡報、README、Demo 影片
- 最後：無痕測試所有連結與備援影片

## 砍功能順序

1. 真實推播服務
2. 多檔股票
3. 持股重要性第二問
4. Bedrock 動態文案
5. Database 持久化

不可砍：一鍵回饋、Portfolio 更新、官方 evidence 與產品故事。
