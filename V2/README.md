# Mindfolio Time Machine V2

> 從 300 檔股票重建五檔投資軌跡，讓陌生用戶先匿名獲得價值，再認領報告、明確確認持股並進入 Portfolio Radar。

V2 不再是固定五檔歷史選擇題。使用者可以從 CMoney 熱門推薦開始，也能搜尋主辦方 300 檔股票資料庫；每檔只需提供買進月份、價格區間或實際價格，以及仍持有或賣出月份。`Portfolio Reconstruction Engine` 會驗證價格合理性、處理公司行動、重建投報率並生成投資指紋。

## 定位：為什麼這不是 FAQ 型 AI

這不是一個你去「問問題」的聊天機器人，是一個你去「玩」的 2025 投資時光機——**零 prompt**。選 5 檔記得的股票、給模糊的買賣記憶，就拿到投資人格、投報率與一張可分享的卡。

- **AI 只是傳播層**：Bedrock 只把已算好的結果寫成人格文案，不做計算、不給投資建議。
- **護城河是 Reconstruction Engine**：把「大概三月買的吧」變成經行情驗證、公司行動還原、附可信度分數的結構化重建事件——單純 LLM 包裝做不到的技術資產。
- **North Star：Verified Holding Activation**——完成重建、明確同意，且成功保存
  至少一檔「仍持有」關係的人數。CMoney 不用叫使用者連券商，就取得使用者
  明確確認的持股關係。

10x 陌生用戶靠兩件事：**匿名分享卡**（病毒獲客，不露持股金額）＋ **Progressive Profiling**（免登入快測 → 註冊完整回放 → 確認持股解鎖雷達）。完整論述見 [產品命題](docs/00_PROJECT_CHARTER.md) 與 [成長漏斗](docs/04_GROWTH_AND_SALES_FUNNEL.md)。

## 成長漏斗 ↔ API 端點

每支後端端點都對應漏斗的一個階段，沒有肥肉：

| 漏斗階段 | API | 為什麼必要 |
|---|---|---|
| 進場（冷流量） | `GET /stocks/popular`、`search` | 讓陌生人低門檻挑熟悉的股票 |
| 資料品質 | `GET /stocks/{id}/months/{ym}/envelope`、`POST /reconstructions/validate` | 把模糊記憶變成具行情合理性與可信度的重建資料、擋亂填——「不只是娛樂測驗」的關鍵 |
| 爽點＋病毒鉤子 | `POST /reconstructions/complete` | 回傳人格／報酬／指紋／分數＋分享卡 |
| Activation | `POST /auth/session`、`POST /reports/{id}/claim` | 邀請碼換短效 session，將匿名報告歸屬會員 |
| North Star（資產） | `POST /reports/{id}/confirmed-holdings` | 第二次明確同意後留下確認持股關係 |
| 留存 | `GET /me/dashboard`、卡片 feedback、event batch | Radar、可追溯證據、低門檻回饋與重試安全事件 |

> **一句話 pitch**：陌生人把模糊記憶變成**經行情驗證的投資重建 + 可分享的人格**，並主動確認仍持有的股票；AI 負責解讀，護城河是重建引擎。API 合約細節見 [前後端架構](docs/09_FRONTEND_BACKEND_ARCHITECTURE.md)。

## 技術架構

正式 V2 採前後端分離。前端使用 **React + TypeScript**；後端統一使用 **FastAPI + Python**，讓行情計算、資料驗證、Portfolio Fingerprint、AI narrative 與離線模型共用同一個 Python runtime。**V2 vertical slice 已完成前後端串接；靜態 `demo/` 保留為視覺與提案 reference。**

```text
React + TypeScript Frontend
  → FastAPI REST API
      → File Market Catalog
      → Reconstruction & Scoring Services
      → AI Narrative Service
      → PostgreSQL Confirmed Holdings
      → [future] Approved Model Inference / Live CMoney Data
```

目前 `demo/` 是靜態 UX reference，內嵌資料與前端計算只用來示範流程，不代表正式安全邊界。正式版的價格驗證、報酬、可信度、人格向量與 AI context 必須全部由 FastAPI 重算。

## 目前完成範圍

- **`apps/api`（後端 API）：P0 已完成** — 包含行情重建、短效 session、匿名報告認領、持股授權、Portfolio Radar aggregate、卡片偏好與 idempotent event batch（共 12 支 `/api/v2` 端點：獲客 6 + 留存 6）；deterministic 引擎與 AI fallback 不依賴 Bedrock 可用性；Python suite 共 60 tests 綠。
- `packages/mindfolio-core`：API 與離線訓練共用的 deterministic domain（envelope、reconstruction、validation、models）。
- **`apps/web`（正式前端）：Acquisition + Retention P0 已完成** — Landing、300 檔搜尋、逐檔重建、匿名人格結果、報告認領、獨立持股授權與四模組 Portfolio Radar；React tests、strict TypeScript build 與 ESLint 零警告通過。
- `apps/ai-training`：離線模型 scaffold（feature 契約 + CLI 狀態）；目前未訓練模型，也不產生假 metrics。
- 根目錄 workspace、Python 共用 virtual environment 設定與前後端測試／建置指令。

部署程式已完成：`api + web + postgres` 可由 Docker Compose 在單一 EC2
執行，且本機容器驗收已通過。Bedrock `openai.gpt-oss-120b` Converse
已完成線上驗證與後端整合；本機可用 Bearer token，正式部署改用 IAM
Role，所有失敗路徑保留 deterministic fallback。尚未完成的是實際 EC2
上線、HTTPS／網域、CMoney SSO、離線模型訓練與即時行情 feed
（操作見 [部署決策](docs/11_DEPLOYMENT.md)）。

## 核心閉環

```text
熱門推薦／300 檔搜尋
→ 自選五檔熟悉股票
→ 買進月份＋區間或實際價格
→ 仍持有／賣出月份
→ 價格異常驗證＋公司行動校正
→ 投報率＋投資人格＋資料可信度
→ 匿名分享
→ 明確同意
→ 只將「仍持有」寫入 LEO Demo Portfolio
```

Demo 以邀請碼換取短效 session，完成匿名報告認領、獨立持股授權與
Portfolio Radar 閉環；正式產品仍需將邀請碼入口替換為 CMoney SSO，並由
既有會員系統提供 identity 與授權生命週期。

## 快速入口

- [可操作 Demo](demo/index.html)
- [文件中心](docs/README.md)
- [資料生成與來源](data/README.md)
- [資料庫快照產生器](tools/build_market_catalog.py)
- [前後端分離架構](docs/09_FRONTEND_BACKEND_ARCHITECTURE.md)
- [AI Training 計畫](docs/10_AI_TRAINING_PLAN.md)
- [部署決策](docs/11_DEPLOYMENT.md)
- [V2 團隊共用實作 Spec](docs/12_V2_END_TO_END_SPEC.md)
- [Time Machine × Portfolio Radar 整合需求 Spec](docs/13_ACQUISITION_RETENTION_INTEGRATION_SPEC.md)
- [本機開發方式](DEVELOPMENT.md)

## Demo 能力

- 依 CMoney 同學會瀏覽人數顯示熱門股票。
- 搜尋 300 檔股票代號、名稱與產業。
- 每檔可選 2025 任一有行情的買進月份。
- 價格可選月內偏低／中間／偏高區，或輸入實際成交價。
- 手動價格超出該月高低範圍時不允許送出。
- 已賣出可選賣出月份與估算／實際價格；仍持有則計算至 12/31。
- 以還原因子校正拆股、除權息後的可比較報酬。
- 產出 Portfolio Fingerprint、人格、情境決策力與資料可信度。

## 重要聲明

月份與價格來自使用者回憶，結果是重建估算，不是券商交易證明。價格合理性檢查只能攔截明顯亂填，不能證明交易真的發生。人格不是心理診斷，分數不代表未來績效，內容不構成投資建議。
