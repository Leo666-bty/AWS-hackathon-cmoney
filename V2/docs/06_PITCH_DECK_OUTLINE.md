# Pitch Deck Outline

| 頁 | 標題 | 核心訊息 |
|---:|---|---|
| 1 | CMoney 最懂股票，卻還不知道陌生用戶持有什麼 | 個人化的瓶頸是第一筆持股資料 |
| 2 | FAQ 要使用者先想問題，連券商又要求太多 | 需要 Zero Prompt、先給價值的陌生開發入口 |
| 3 | Mindfolio Time Machine | 用五檔熟悉股票重建個人投資軌跡 |
| 4 | 熱門引導＋300 檔搜尋 | 容易開始，又能連到真實經驗 |
| 5 | 月份＋區間＋實際價格 | Progressive profiling，不要求精確交易明細 |
| 6 | Live Demo：故意輸入亂價 | 當月行情 envelope 即時阻擋異常 |
| 7 | 不是 LLM 包裝：Portfolio Reconstruction Engine | 模糊記憶經行情驗證、公司行動還原與可信度計算 |
| 8 | 可實作 AI Training | Market Regime＋Anomaly 模型，不虛構持股預測 |
| 9 | confirmed holding 邊界 | 只有明確選擇仍持有才寫入 Portfolio |
| 10 | Time Machine × Portfolio Radar | V2 分享獲客 → 註冊認領 → V1 能力留存 → 回訪 |
| 11 | CMoney 的資料護城河 | 300 檔只是 Demo，可擴充法人、估值與社群訊號 |
| 12 | Closing | 人格讓人進來，技術讓資料可信，雷達讓人留下 |

## Opening

> 如果請陌生人上傳完整庫存，他會離開；如果只問五檔熟悉股票、大概月份與價格，他願意先換一份看得見自己的報告。

## 為什麼不是 FAQ 型 AI

> FAQ 要使用者先有問題；Mindfolio 讓使用者先玩。AI 不是產品本身，它只把 verified result 說成人話；真正的護城河是把模糊交易記憶轉成可信持股事件的 Reconstruction Engine。

## 技術一句話

> React 負責讓陌生用戶低門檻完成重建；FastAPI 先驗證並以 deterministic
> engine 計算結果；離線 KMeans／IsolationForest 再補上買進月份市場情境，
> AI service 最後才把已驗證證據轉成結構化 Deep Dive。

## 成長一句話

> 匿名人格卡讓每個結果成為下一個陌生人的入口；Progressive Profiling 再用完整回放與 Portfolio Radar，逐層把匿名流量轉成會員與明確確認的持股資料。

React × FastAPI + AI P0 已完成（14 支 API、V2 Python 67 tests、React 6 tests、
production build 與 lint）。Live Demo 直接操作正式 React 流程，並可用
`/api/v2/docs` 證明 validation／complete 是後端重算；`V2/demo/` 只作為
presentation-only 的靜態視覺 reference。

## Closing

> 這不是一個你去問問題的聊天機器人，而是一個你去玩的 2025 投資時光機。人格讓人進來，重建引擎讓資料可信，Portfolio Radar 讓人留下。
