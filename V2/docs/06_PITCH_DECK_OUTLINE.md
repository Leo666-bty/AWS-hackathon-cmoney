# Pitch Deck Outline

| 頁 | 標題 | 核心訊息 |
|---:|---|---|
| 1 | CMoney 最懂股票，卻還不知道陌生用戶持有什麼 | 個人化的瓶頸是第一筆持股資料 |
| 2 | 連券商與完整表單太早、固定測驗又太淺 | 需要兼顧低門檻與資料品質 |
| 3 | Mindfolio Time Machine | 用五檔熟悉股票重建個人投資軌跡 |
| 4 | 熱門引導＋300 檔搜尋 | 容易開始，又能連到真實經驗 |
| 5 | 月份＋區間＋實際價格 | Progressive profiling，不要求精確交易明細 |
| 6 | Live Demo：故意輸入亂價 | 當月行情 envelope 即時阻擋異常 |
| 7 | React × FastAPI Portfolio Reconstruction Engine | 前端體驗與後端可信計算分離 |
| 8 | 可實作 AI Training | Market Regime＋Anomaly 模型，不虛構持股預測 |
| 9 | confirmed holding 邊界 | 只有明確選擇仍持有才寫入 Portfolio |
| 10 | 獲客與留存飛輪 | 分享 → 註冊 → 持股雷達 → 回訪 |
| 11 | CMoney 的資料護城河 | 300 檔只是 Demo，可擴充法人、估值與社群訊號 |
| 12 | Closing | 人格讓人進來，技術讓資料可信，雷達讓人留下 |

## Opening

> 如果請陌生人上傳完整庫存，他會離開；如果只問五檔熟悉股票、大概月份與價格，他願意先換一份看得見自己的報告。

## 技術一句話

> React 負責讓陌生用戶低門檻完成重建；FastAPI 先驗證、計算與執行 Market Regime／Anomaly inference，最後才讓同一個 Python 環境中的 AI service 生成文案。

目前若尚未完成後端，簡報必須使用「目標架構」與「下一步實作」，不可把靜態 Demo 描述為已上線的 FastAPI 系統。

## Closing

> CMoney 的十倍用戶成長，不只需要更好的內容，也需要一個讓陌生人願意留下第一筆高品質持股資料的入口。
