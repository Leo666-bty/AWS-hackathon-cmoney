# 150-Second Demo Runbook

## 0–20 秒：問題與入口

> 「陌生用戶不會先連券商，但他願意用五檔熟悉股票，看看自己的投資人格。」

指出首頁的 300 檔資料庫、月份價格 envelope 與公司行動調整，點「匿名開始重建」。

## 20–50 秒：熱門與自選

1. 說明熱門名單依同學會瀏覽人數排序，不是買進推薦。
2. 搜尋一檔股票代號，證明不是固定題庫。
3. 使用熱門捷徑補滿五檔，進入重建。

## 50–100 秒：月份、價格與防亂填

至少示範三種情境：

- 一檔選買進月份＋偏低區＋仍持有。
- 一檔輸入落在當月範圍內的實際價格，展示通過驗證。
- 一檔先輸入超出行情的價格，展示阻擋，再修正。
- 一檔標記已賣出並選賣出月份。

說明使用者輸入是原始成交價，報酬計算會轉為公司行動調整後價格。

## 100–130 秒：技術 Output

結果頁依序指出：

1. 五檔等權重推估報酬。
2. confirmed holdings 只來自「仍持有」。
3. 重建可信度不是投資能力或交易證明。
4. 口頭說明 Entity Resolution → Temporal Validation → Corporate Action →
   Fingerprint Vector；目前結果頁沒有獨立 pipeline 圖。
5. 不同股票、月份與價格會改變人格與向量。

## 130–150 秒：成長閉環

複製匿名分享文案，指出不包含持股與報酬明細。勾選 consent 後點
「確認並建立庫存」，展示後端只接受重新驗證後的 `holding_candidates`；Compose
部署會寫入 PostgreSQL，本機未設定 `DATABASE_URL` 時則是重啟即清空的 memory store：

> 「人格負責讓陌生人進來；重建引擎負責取得高品質資料；今天先完成明確持股，下一步才由持股雷達讓他持續回來。」

現行按鈕使用固定 Demo identity `LEO`，沒有登入、報告認領或 Portfolio Radar
頁面；這三項只能作為下一階段產品方向說明。

## 禁止說法

- 這些是 CMoney 推薦買進的熱門股票。
- 通過價格檢查就代表交易是真的。
- 測驗分數代表真實投資能力。
- Demo 已經串接使用者券商帳戶。
- 靜態 `V2/demo/` 畫面背後已經完成正式 FastAPI 串接。

## 現階段展示口徑

正式 Live Demo 優先使用 `docker compose up -d --build`，讓 nginx、FastAPI 與
PostgreSQL 都符合部署拓撲。本機 UI 排練也可先以 `make dev-api` 啟動 FastAPI，
再以 `make dev-web` 啟動 React，但預設 confirmed holdings 只存在 memory store。
兩種方式的熱門／搜尋、月份 envelope、validation、complete、AI narrative 與
confirmed holdings 都走 `/api/v2`。`V2/demo/` 只能作為 presentation-only 的靜態
視覺 reference，不是 runtime 降級路徑；若現場展示，必須明說其瀏覽器計算不是
正式金融結果。
