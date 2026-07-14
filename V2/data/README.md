# V2 Market Database Snapshot

## 原始來源

原始資料存放於 `V2/data/Delivery_Hackathon_DataPackage_20260624/`（gitignored，不進 remote）。V2 讀取：

- `01_Price_Valuation_2025.csv`：每日原始開高低收，用來檢查使用者記得的成交價格。
- `03_Return_Rate_2025.csv`：每日還原收盤價，用來建立公司行動調整因子。
- `09_Wide_Table_Summary_One_Row_Per_Stock_2025.csv`：股票、產業及同學會瀏覽人數。

## 生成方式

執行 `V2/tools/build_market_catalog.py --json`，產生前端用的 `V2/demo/market-data.js` 與後端讀取的 `V2/data/market-catalog.json`。輸出包含：

- 300 檔股票主檔。
- 依同學會瀏覽人數排序的熱門股票。
- 每檔每月原始最低、最高與月末收盤。
- 每月月末還原收盤與 adjustment factor。
- 月內 adjustment factor 變動超過 5% 的公司行動旗標。
- 公司行動前後的原始價格 regime，供實際價格選擇正確還原因子。

這是版本化的 2025 靜態 market snapshot。正式 React runtime 不直接下載整份
catalog，而是由 FastAPI 啟動時載入 `market-catalog.json`，再透過熱門、搜尋與
月份 envelope API 回傳必要資料。PostgreSQL 不保存市場行情，只保存使用者
明確同意的 confirmed holdings；`demo/market-data.js` 只供 presentation-only 的
靜態視覺 reference，不是正式 runtime fallback。

## 價格與報酬

使用者輸入的實際價格先以該月原始高低範圍驗證，再轉為可比較價格：

```text
adjustment_factor = 月末還原收盤價 / 月末原始收盤價
adjusted_user_price = user_price × adjustment_factor
estimated_return = adjusted_exit_price / adjusted_entry_price - 1
```

若選擇價格區間，系統分別使用月內範圍的 1/6、1/2、5/6 位置作為偏低、中間、偏高估計。若賣出時未輸入實際價格，使用該月最後交易日還原收盤價。

若公司行動發生在月內，合併後的原始高低範圍可能失真，因此不接受區間估計；使用者必須輸入實際價格或改選月份。引擎再依價格落入的 pre/post-action regime 選擇 adjustment factor。

## 限制

- 月份級輸入不等於精確交易日。
- 公司行動發生在月中時，月末 adjustment factor 仍是近似校正，因此降低可信度。
- 未計交易稅、手續費、滑價、分批交易與部位權重。
- 五檔 Demo 採等權重，不能描述成使用者真實總資產報酬。
