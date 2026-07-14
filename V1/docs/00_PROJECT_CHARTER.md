# Project Charter

## 專案

**Mindfolio AI — Reverse Portfolio Onboarding for 籌碼 K 線**

## 問題

CMoney 已嘗試 WebUI ChatGPT 類型產品，但使用者不會持續想問題、輸入 Prompt 或長時間對話。完整建庫同樣要求使用者先付出，還伴隨財務隱私疑慮。

## 核心判斷

問題不是模型不會回答，而是互動順序錯誤：產品要求使用者在看到價值之前先聊天、填表或交出資料。

## 解法

> AI 在籌碼 K 線的既有頁面先顯示有證據的洞察，再以一次點擊確認「持有／觀察／不相關」。

這個模式稱為 **Reverse Portfolio Onboarding**：用洞察換確認，不用問題換資料。

## TA

已使用籌碼 K 線查股或維護自選股，但沒有在 CMoney 建立或持續維護庫存的台股投資人。Demo Persona 統一為 **LEO**。

## 三天 MVP 驗證問題

1. 使用者是否願意在看見洞察後，用一次點擊確認至少一檔持股？
2. 確認後的持股情境，是否能讓同一份籌碼資料變得更個人化？
3. 不使用聊天、截圖或完整表單，是否仍能建立最小可用 Portfolio Context？

## MVP 成功定義

完成一條可操作且可量測的閉環：自選股 → 廣達個股頁 → 法人／社群／新聞證據 → LEO 一鍵確認持股 → 低門檻 Concern Signal → 情境式 AI 追問 → 我的庫存 → 互動 Dashboard。

三天交付不是只有畫面：正式 MVP 應完成 React、FastAPI、PostgreSQL、事件寫入與部署；`apps/web/prototype` 是共用互動 reference 與離線備援。

## 明確不做

- 獨立聊天頁與自由輸入 Prompt；只保留卡片內的建議追問
- 上傳券商截圖
- 推測精確成本、股數、報酬或總資產
- 個人焦慮診斷或虛構分數；只收使用者明確回覆的 Concern Signal
- 股價預測、買賣建議
- 模型訓練、RAG、向量資料庫、Agent framework
- 完整推播服務；MVP 只驗證站內情境卡，推播為下一階段通路

## Must-have MVP Slices

- 前台：自選股、個股四分頁、情境卡、個人庫存。
- AI：一張可追溯證據的背離卡，以及三個情境式建議追問。
- 資料：官方市場／法人／社群資料；新聞暫用清楚標示的 Demo Feed。
- 互動：關係回饋與 Concern Signal 都產生可同步事件。
- 後台：最小 Dashboard 顯示曝光、回饋、持股確認與事件 outbox。

## 官方資料限制

主辦方資料能支撐市場與社群情境，不能直接支撐個人持股推論。個人持股必須來自 LEO 的明確確認；產品行為資料在 Demo 中由互動即時產生，不假裝存在於官方 CSV。
