# Data & Guardrails

## 資料分工

| 資料 | 用途 |
|---|---|
| 每日原始高低收 | 驗證使用者記得的實際價格 |
| 每日還原收盤 | 公司行動調整與可比報酬 |
| 股票／產業主檔 | 搜尋與分散度計算 |
| 同學會瀏覽人數 | 熱門推薦排序 |
| 使用者月份／價格 | 重建買賣事件 |
| 使用者仍持有選擇 | 唯一 confirmed holding 來源 |

## 三層驗證

1. **Schema validation**：月份、價格、狀態格式完整。
2. **Temporal validation**：賣出月份晚於買進月份。
3. **Market envelope validation**：實際價格落在該月原始最低與最高之間。

未來正式版可以增加 device rate limit、重複 pattern、極端輸入與 bot detection，但不能把異常偵測說成交易證明。

## 可以說

- 「價格落在該月市場行情範圍內。」
- 「依月份與價格重建的推估報酬為 X%。」
- 「使用者主動確認 12/31 仍持有這檔股票。」
- 「公司行動月份已降低重建可信度。」

## 不可以說

- 「我們證明他真的以這個價格成交。」
- 「這是使用者真實總資產報酬。」
- 「高分代表未來能打敗市場。」
- 「熱門推薦等同 CMoney 買進推薦。」

熱門標籤只能描述「同學會瀏覽熱度」，介面與簡報不得把它寫成投資推薦。

## 目前資料與資料庫邊界

正式 React runtime 由 FastAPI repository 在啟動時載入
`data/market-catalog.json`；前端只取熱門、搜尋與單月 envelope，不下載整份月行情，
也不自行計算驗證結果。靜態 `demo/market-data.js` 只作為 presentation-only 的
視覺 reference，不是正式 runtime fallback。

目前 PostgreSQL 只有 `confirmed_holdings`：`user_id`、`stock_id`、固定
`source=user_confirmed` 與 `confirmed_at`。市場主檔與月行情不進 PostgreSQL，
reconstruction input／result、匿名 session 與 event 也尚未持久化。

未來導入登入與報告認領時，anonymous reconstruction、member profile 和
confirmed holding 必須使用清楚分離的 identifier／table；不能把搜尋、測驗選股或
未同意的重建事件自動轉成正式 Portfolio。

## 前後端信任邊界

前端送出的是使用者聲明與 UI 狀態，不是可信計算結果。以下欄位一律由 FastAPI 產生：

- 價格是否落在當月 envelope。
- company-action regime 與 adjustment factor。
- adjusted entry／exit price。
- reconstructed return。
- reconstruction confidence。
- Portfolio Fingerprint vector 與 persona code。
- 可以交給 AI 的已驗證 context。

前端送來的 `return`、`score`、`confidence`、`persona` 或 `factor` 即使存在也必須忽略，避免竄改。
