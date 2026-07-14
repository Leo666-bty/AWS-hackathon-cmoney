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

## 正式資料庫邊界

Demo 使用 `market-data.js` 快照；它只能作為 UX reference。正式版由 FastAPI 從 repository 讀取資料，前端不下載完整月行情資料庫，也不自行計算驗證結果。資料表建議：

- `stock_master`：代號、名稱、產業。
- `monthly_price_envelope`：年月、原始高低、月末原始／還原價、公司行動旗標。
- `anonymous_portfolio_event`：session、股票、買進月、價格模式、狀態、可信度。
- `confirmed_holding`：只有明確同意後才從匿名事件建立。

匿名事件與會員持股必須分表，避免測驗輸入自動污染正式 Portfolio。

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
