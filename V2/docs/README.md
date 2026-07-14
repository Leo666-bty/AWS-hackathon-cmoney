# V2 Documentation Hub

| 文件 | 用途 |
|---|---|
| [`00_PROJECT_CHARTER.md`](00_PROJECT_CHARTER.md) | 命題、價值主張、範圍與成功條件 |
| [`01_PRODUCT_AND_UX.md`](01_PRODUCT_AND_UX.md) | 完整體驗、頁面與互動狀態 |
| [`02_QUIZ_PERSONALITY_AND_SCORING.md`](02_QUIZ_PERSONALITY_AND_SCORING.md) | 題目、四軸人格、報酬與分數公式 |
| [`03_DATA_AND_GUARDRAILS.md`](03_DATA_AND_GUARDRAILS.md) | 官方資料來源、可說與不可說 |
| [`04_GROWTH_AND_SALES_FUNNEL.md`](04_GROWTH_AND_SALES_FUNNEL.md) | 社群響應、銷售漏斗、留存與 KPI |
| [`05_DEMO_RUNBOOK.md`](05_DEMO_RUNBOOK.md) | 150 秒 Live Demo 腳本 |
| [`06_PITCH_DECK_OUTLINE.md`](06_PITCH_DECK_OUTLINE.md) | 評審簡報故事線 |
| [`07_IMPLEMENTATION_PLAN.md`](07_IMPLEMENTATION_PLAN.md) | 三天實作優先序與切割線 |
| [`08_TECHNICAL_INNOVATION.md`](08_TECHNICAL_INNOVATION.md) | Portfolio Reconstruction Engine 與正式 API 邊界 |
| [`09_FRONTEND_BACKEND_ARCHITECTURE.md`](09_FRONTEND_BACKEND_ARCHITECTURE.md) | 前後端分離、FastAPI 模組、API contract 與部署邊界 |
| [`10_AI_TRAINING_PLAN.md`](10_AI_TRAINING_PLAN.md) | 可實作模型、features、labels、artifact、inference 與評估 |
| [`11_DEPLOYMENT.md`](11_DEPLOYMENT.md) | 部署決策：單一 EC2 上以 Docker Compose 執行 web + api + postgres |
| [`12_V2_END_TO_END_SPEC.md`](12_V2_END_TO_END_SPEC.md) | V2 React × FastAPI vertical slice、契約、狀態與驗收條件 |
| [`13_ACQUISITION_RETENTION_INTEGRATION_SPEC.md`](13_ACQUISITION_RETENTION_INTEGRATION_SPEC.md) | Time Machine 獲客銜接 Portfolio Radar 留存的需求基準與後續 SDD 拆分 |

> 後端 SDD 功能規格（spec/plan/tasks）在 [`api/`](api/)：001 資料地基、002 重建引擎、003 確認持股。

## Source of truth

- 產品命題：`00_PROJECT_CHARTER.md`
- 計算與人格：`02_QUIZ_PERSONALITY_AND_SCORING.md`
- 數據聲明：`03_DATA_AND_GUARDRAILS.md`
- 現場操作：`05_DEMO_RUNBOOK.md`
- 技術亮點：`08_TECHNICAL_INNOVATION.md`
- 系統架構：`09_FRONTEND_BACKEND_ARCHITECTURE.md`
- AI Training：`10_AI_TRAINING_PLAN.md`
- 互動 reference：`../demo/`
- 開發共識與驗收：`12_V2_END_TO_END_SPEC.md`
- 獲客到留存整合需求：`13_ACQUISITION_RETENTION_INTEGRATION_SPEC.md`
