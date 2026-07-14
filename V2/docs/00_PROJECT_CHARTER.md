# Project Charter

## 專案名稱

**Mindfolio Time Machine — Portfolio Reconstruction Engine**

> 讓陌生用戶用五檔熟悉股票重建 2025 投資軌跡，先得到人格與投報率，再主動確認仍持有的股票。

## 問題

CMoney 擁有大量市場資料，但陌生用戶不會為了未知價值先登入、連券商或填完整庫存。固定題目的娛樂測驗容易分享，卻無法累積真實持股，也不足以展現技術能力。

## 解法

把「人格測驗」升級為持股重建流程：

1. 熱門推薦降低開始成本。
2. 300 檔搜尋讓內容貼近個人經驗。
3. 月份與價格區間降低回憶門檻。
4. 時間價格驗證攔截明顯異常輸入。
5. 還原因子讓公司行動前後價格可比較。
6. 人格與匿名分享負責獲客，仍持有確認負責 Portfolio 建檔。

## North Star

**Verified Holding Activation**：完成重建並主動標記至少一檔「2025-12-31 仍持有」的匿名或已註冊使用者數。

## Demo 必須證明

- 熱門推薦是由資料排序，不是寫死行銷名單。
- 任意五檔都能完成月份級買賣重建。
- 亂填價格會被月份行情範圍拒絕。
- 公司行動不會直接造成錯誤投報率。
- Result 同時顯示報酬、可信度與技術 pipeline。
- 只有使用者明確選擇「仍持有」才形成 confirmed holding。

## 技術決策

- 正式產品採前後端分離，Frontend 使用 React + TypeScript。
- React Frontend 不持有完整市場資料，也不負責正式計算。
- Backend 使用 FastAPI + Python，統一承擔驗證、報酬、Fingerprint、人格與 AI orchestration。
- deterministic finance calculation 與 AI 共用 Python environment，但維持不同 service boundary。
- Offline AI training 與 FastAPI 共用 feature definitions 與 model contract，不在 request path 訓練。
- 目前靜態 Demo 只驗證 UX；不能宣稱 FastAPI 已完成。

## 非目標

- 不驗證券商真實成交紀錄。
- 不從價格合理推論交易一定存在。
- 不把估算報酬當作真實總資產績效。
- 不做買賣建議、未來預測或心理診斷。
