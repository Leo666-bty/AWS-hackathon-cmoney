# Changelog & Product Journey

## 2026-07-15 — V2.12：AI Deep Dive 稽核收尾與文件全面對齊

- 對 V2.11 AI 功能碼做嚴苛程式稽核：確認跨會員權限隔離、月份 key 正規化、無 secret／SQLi 皆正確；修正四個 hardening bug。
- `save_ai_report` 快取寫入失敗改為 best-effort：已產生的報告仍回傳，不再因缺 migration 欄位或 DB 抖動而 503 丟棄有效報告。
- AI cache key 納入 artifact `content_sha256`：重訓即使未 bump `MODEL_VERSION` 也會失效，消除 stale-forever。
- `_fallback_report` 加上例外邊界（退回最小報告），兩支 AI 端點攔截 `ValidationError`，兌現「一定有 deterministic fallback、不裸 500」的文件保證。
- 補雙身份 cross-member 隔離測試與快取失敗測試；Python 67 tests 綠。
- 全面對齊所有 `V2/` Markdown 與根 `README/CHANGELOG`：端點數（12→14）、測試數（60→65／67）、ai-training「未訓練」敘述、部署拓撲（Vercel→單機 EC2 Compose）、Bedrock「已線上驗證」過度宣稱、EC2 上線狀態的三方不一致、Bedrock 完整 model ID，以及根 README 的 demo 連結改指本機啟動。
- 未處理（進 `15_OPTIMIZATION_CHECKLIST §2.6` backlog，均屬訓練期或 Bedrock-only、不影響 Demo）：guardrail 子字串誤擋、`features.py` NaN fallback、pipeline balance-gate provenance。

## 2026-07-15 — V2.11：AI P0 實作、前後端整合與可驗證市場情境

- 將 `14_AI_MINIMAL_INTEGRATION_SPEC.md` 從規劃更新為已實作／已驗證，並同步修正 Project Charter、Pitch、Implementation、Architecture、Training、Deployment 與 End-to-End Spec。
- 完成官方 2025 CSV 的 monthly feature pipeline，實際產出 3,584 個 stock-month samples；features 涵蓋報酬、波動、最大回落、成交量、週轉率、法人流量比例與全站社群訊號。
- 完成 KMeans Market Regime 與 IsolationForest anomaly training；選模加入最大群集 75% balance gate，避免只追求 silhouette 而產生單一群集占 89.5% 的退化結果。
- 發布版本化 `market-context-2025-v1.json`，包含 3,584 筆預先評分 context、真實 metrics、feature/model version 與 SHA-256 checksum；training features 與 joblib 保持可重建且不進 runtime image。
- FastAPI 新增 fail-soft `MarketContextRepository`，以 `stock_id:YYYY-MM` O(1) 查表；production API 不安裝或載入 sklearn，artifact 缺失、版本錯誤或 checksum 不符時不阻斷原本 reconstruction。
- 新增 report-owner-only 的 `POST /reports/{report_id}/ai-report` 與 `POST /reports/{report_id}/questions`，支援結構化 AI Deep Dive、PostgreSQL cache、evidence refs、Bedrock schema guardrail 與 deterministic fallback。
- AI 問答僅接受 `why-persona`、`most-influential-trade`、`why-anomalous-month` 三個 server-defined question IDs，不加入自由聊天框。
- React `/result` 新增 AI Deep Dive teaser；`/app` 新增 summary、strength、watchout、market moment、source badge 與三個低門檻問題 chips，並完成 Zod API contract 與互動事件。
- 新增 `002_ai_report_cache.sql`，Docker image 納入 pre-scored artifact，Compose schema 改為有序目錄掛載；既有 PostgreSQL volume 仍需手動套用 migration。
- 恢復 `15_OPTIMIZATION_CHECKLIST.md`，明確標示為 Post-P0 backlog，不屬本次三天 MVP 開發範圍。
- 補齊本機手動驗證流程與 DevTools API sequence；修正 Docker context 排除 artifact，以及重建月份 `01` 與 artifact key `2025-01` 不一致的 lookup 問題。
- 最終驗證：Python 65 tests、React 6 tests、TypeScript、Vite production build、ESLint、Docker Compose config 與 Git diff whitespace check 全數通過。

## 2026-07-15 — V2.10：AI 最小整合需求規格

- 新增 `14_AI_MINIMAL_INTEGRATION_SPEC.md`，定義不改現有 React、FastAPI、`mindfolio-core` 與 PostgreSQL 拓撲的 AI 增量方案。
- 將 ML 限定於 Market Regime clustering 與 anomaly detection，維持 deterministic reconstruction 為金融事實來源。
- 定義 claim 後 lazy generation 的完整 AI 報告、evidence-based 單輪問答、artifact contract、fallback、guardrails 與 persistence 增量。
- 更新 AI Training Plan 與文件中心索引；本版僅交付規格，尚未訓練模型或實作 online inference。

## 2026-07-15 — V2.9：獲客 × 留存閉環與單機部署整合

- 完成 Time Machine 匿名獲客到 Portfolio Radar 留存的 P0 vertical slice：短效 session、報告認領、獨立持股同意、個人化 dashboard、卡片回饋與 idempotent event batch。
- React 正式前端新增啟用流程與 Portfolio Radar；FastAPI 新增 retention repository／service／router，並以 PostgreSQL 保存報告、持股與互動事件。
- 整合單一 EC2 的 Docker Compose 部署，包含 Nginx、FastAPI、PostgreSQL、health check、production session secret 與 Bedrock IAM／fallback 契約。
- 合併遠端部署文件與本地留存功能，修正 README 的完成範圍與測試數，消除「Radar 尚未實作」的過時敘述。
- 發布前驗證：Python 64 tests、React 3 tests、ESLint、TypeScript production build 與 `docker compose config` 全數通過。

## 2026-07-14 — V2.8：強化非 FAQ 定位、10x 機制與技術護城河敘事

- 將 Zero Prompt、AI 敘事層與 Reconstruction Engine 技術護城河寫入 Project Charter。
- 明確定義匿名分享卡 referral loop 與 Progressive Profiling value-for-data ladder。
- 將 Verified Holding Activation 對齊 CMoney 從陌生流量取得明確持股資料的 North Star。
- Pitch Deck 故事調整為 Time Machine 獲客、Portfolio Radar 留存；AI 負責解讀，金融真相仍由可重算引擎產生。
- 本次只整理附件中的產品論述與既有文件，未修改產品功能或程式。

## 2026-07-14 — V2.7：定義 Time Machine 獲客 × Portfolio Radar 留存需求

- 新增 `13_ACQUISITION_RETENTION_INTEGRATION_SPEC.md` 作為後續 SDD 的 umbrella requirements baseline。
- 確認 V2 仍是唯一主要專案與 runtime；V1 僅作為 Moment Engine、Action Card、Portfolio 與事件語意參考。
- 定義匿名報告認領、會員啟用、持股同意、Portfolio Radar、Market Moment、Bedrock 敘事與事件資料邊界。
- 建立 FR／NFR、狀態轉移、驗收情境、隱私要求與 P0／P1 切割線。
- 規劃後續 SDD feature 004–007；本次只更新需求文件，未開始留存功能實作。

## 2026-07-14 — V2.6：圖卡提前與決策力雷達圖

- 將人格分享圖卡移到結果頁上方，優先於投報、持股與情境決策分數呈現。
- 新增四軸情境決策力雷達圖，依報酬結果、進場位置、報酬捕捉與資料完整度即時計算。
- 雷達圖將各指標換算為相同比例，並保留原始分數卡供使用者核對。

## 2026-07-14 — V2.5：結果分享改用八型人格圖卡

- 將 `demo/assets/personality-cards` 八張直式圖卡建立為人格圖卡資料表。
- 結果頁依 Portfolio Fingerprint 前三碼自動顯示對應圖卡。
- 分享流程優先使用裝置原生圖片分享；不支援時改為下載圖卡並複製匿名文案。
- 增加獨立下載圖卡與複製文案操作，所有分享內容均不包含持股、價格與報酬明細。

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
