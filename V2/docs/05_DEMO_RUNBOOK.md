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

## 130–150 秒：成長閉環（Time Machine → Portfolio Radar）

複製匿名分享文案，指出不包含持股與報酬明細。接著完整走出兩階段閉環：

1. `complete` 已回傳 report handle（`report_id` + `claim_token`）。到 `/activate`
   輸入邀請碼（demo `demo-leo:LEO`）換取 session token——身份由伺服器端 session
   推導，前端不再夾帶 `user_id`。
2. 以該 session 認領剛才的報告（`POST /reports/{id}/claim`），把獲客結果綁定到會員 `LEO`。
3. 勾選 consent 後確認持股，走 report-scoped 的
   `POST /reports/{id}/confirmed-holdings`：後端只寫入重新驗證後的
   `holding_candidates`，並記錄 `source_report_id`。
4. 進入 `/app` 的 Portfolio Radar：展示 dashboard 的人格/fingerprint、持股、
   priority action card 與 weekly review。

> 「人格負責讓陌生人進來；重建引擎負責取得高品質資料；今天完成明確持股後，持股雷達就讓他持續回來——兩階段今天都已經跑得起來。」

Compose 部署會把持股與 reports/feedback/events 寫入 PostgreSQL；本機未設定
`DATABASE_URL` 時為重啟即清空的 memory store，此時 `complete` 的 report handle 為
`null`，可改以口頭帶過認領步驟。可如實補充：narrative 目前走 deterministic
fallback（`bedrock_enabled` 預設 false），action card 的 `mute` 偏好已被記錄但尚未
改變下一張卡片的排序（未來 Feature 006）。

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
兩種方式的熱門／搜尋、月份 envelope、validation、complete、AI narrative，以及
留存側的 auth/session、report claim、report-scoped confirmed holdings、
me/dashboard、card feedback 與 events batch 都走 `/api/v2`。`V2/demo/` 只能作為
presentation-only 的靜態
視覺 reference，不是 runtime 降級路徑；若現場展示，必須明說其瀏覽器計算不是
正式金融結果。
