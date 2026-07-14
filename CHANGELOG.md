# Changelog & Product Journey

## 2026-07-14 — V2.4：React／FastAPI／AI Training 專案初始化

- 建立 pnpm workspace 與 React + TypeScript + Vite frontend。
- 加入 Router、React Query、typed health client、foundation route 與前端測試。
- 建立 FastAPI application factory、CORS、OpenAPI 與 `/api/v2/health`。
- 建立 API／Training 共用的 `mindfolio-core` domain、feature 與 inference package。
- 建立 offline AI training command 與 artifact metadata contract；尚未訓練模型，不產生虛構 metrics。
- 建立共用 Python virtual environment、測試與 production build baseline。
- 保留 `demo/` 作為 UX reference；正式金融計算與資料信任邊界仍以 FastAPI 為準。

## 2026-07-14 — V2.3：補齊 React 架構與 AI Training 計畫

- Frontend 正式指定為 React + TypeScript，採 route／feature-based structure。
- React server state、wizard draft、field state 與 backend identity 分開管理。
- FastAPI OpenAPI 作為前端 typed client contract。
- 新增 `apps/ai-training` 與 `packages/mindfolio-core` 的目標結構，和 FastAPI 共用 Python environment 與 feature definitions。
- 現有資料可先訓練 Market Regime clustering 與 IsolationForest anomaly detector。
- confirmed holding／內容排序模型延後到累積明確用戶 labels 後；不以瀏覽事件假裝持股 ground truth。
- Bedrock／LLM narrative 被明確定義為 inference orchestration，不冒充模型訓練。

## 2026-07-14 — V2.2：確認前後端分離與 FastAPI 技術決策

- 正式架構定為 Web frontend 與 FastAPI backend 分離。
- Python backend 同一環境承擔資料驗證、金融計算、Portfolio Fingerprint 與 AI narrative。
- 計算與 AI 雖共用 runtime，仍拆成 deterministic services 與 AI service。
- 前端不再被視為正式計算與資料信任邊界。
- 目前靜態 Demo 僅保留為 UX reference；本次只修改文件，尚未實作 FastAPI 或搬移目錄。

## 2026-07-14 — V2.1：從固定測驗升級為 Portfolio Reconstruction Engine

### 為什麼再調整

固定五檔與固定日期雖然容易 Demo，卻只能收集測驗選擇，無法確認陌生用戶真正熟悉或仍持有哪些股票；同時也容易被評審視為純 Landing Page。

### 這次改變

- 熱門股票改由 CMoney 同學會瀏覽人數排序。
- 加入 300 檔股票代號、名稱與產業搜尋。
- 使用者自選五檔，再提供買進月份與價格區間／實際價格。
- 已賣出可選賣出月份；仍持有計算至 2025-12-31。
- 用每月原始高低價檢查明顯亂填。
- 用還原收盤因子調整拆股、除權息後的可比較報酬。
- 新增資料可信度、Portfolio Fingerprint vector 與技術 pipeline。
- 只有明確選擇「仍持有」才形成 confirmed holding。

### 技術定位

> 人格是傳播層；Portfolio Reconstruction Engine 才是資料品質與技術護城河。

## 2026-07-14 — V2：從建庫工具轉向可傳播的投資人格體驗

### 為什麼重做

V1 已解決低門檻取得持股關係的問題，但確認後的 Output 主要是 Portfolio 更新與單一市場洞察。這能證明資料閉環，卻不夠像一個使用者會主動完成、分享並再次回來的產品。

V2 將題目改寫成：

> 如何把 CMoney 的 2025 歷史資料，轉成每個人都想測、想分享、又願意補充真實持股的投資人格體驗？

### 產品轉向

| V1 | V2 |
|---|---|
| 先給洞察，再確認持股 | 先玩歷史決策，再看人格與報酬 |
| 一檔股票、一個關係回饋 | 五檔股票、十個買賣決策、兩個偏好題 |
| Portfolio 由 0 變 1 | 產生可比較、可分享的個人結果 |
| 站內情境卡 | 社群測驗入口＋個人報告＋持續雷達 |
| 核心 KPI：首檔持股確認 | 核心 KPI：完成、分享、註冊、補充持股、回訪 |

### 保留的原則

- 仍採「先提供價值，再要求更多資料」。
- 所有報酬率使用可追溯的 2025 官方資料。
- 不將社群資料描述為個人情緒。
- 不把測驗結果包裝為心理診斷或未來獲利保證。

### 新增的創新亮點

1. **2025 投資時光機**：使用者在共同歷史節點做決策，結果可公平比較。
2. **投資人格四軸**：把交易節奏轉成易理解、易分享的語言。
3. **情境決策力拆解**：分開顯示報酬結果、進場位置、出場捕捉與證據流程。
4. **匿名分享卡**：不公開股票與金額，也能形成社群傳播。
5. **Progressive Profiling**：先匿名測驗，再以完整回放、真實持股雷達逐層換取資料。

## 2026-07-11 ～ 2026-07-13 — V1：Reverse Portfolio Onboarding

- 建立 Mindfolio AI 主線。
- 以 LEO 與 2025-12-31 廣達情境完成互動閉環。
- 確立「候選關係不能當作真實持股」與 Concern Signal 邊界。
- 建立前台 Demo、API contract、資料與 AI 文件、簡報及執行計畫。
- 目前完整封存於 `V1/`。
