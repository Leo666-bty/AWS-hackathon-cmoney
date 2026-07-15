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
| [`14_AI_MINIMAL_INTEGRATION_SPEC.md`](14_AI_MINIMAL_INTEGRATION_SPEC.md) | 不改現有架構的 ML 情境、完整 AI 報告與證據型問答整合需求 |
| [`15_OPTIMIZATION_CHECKLIST.md`](15_OPTIMIZATION_CHECKLIST.md) | P0 之後的安全、部署、模型品質與產品實驗 backlog；不屬本次開發範圍 |
| [`16_PROPOSAL_OUTLINE.md`](16_PROPOSAL_OUTLINE.md) | 黑客松提案大綱（TA／痛點解法／低門檻與回訪／指標／架構與資料應用／評分對映） |
| [`ppt/index.html`](ppt/index.html) | 20 頁 HTML 提案簡報；沿用 V2 UI 視覺，含鍵盤操作、講者提示、總覽與列印版 |
| [`ppt/pitch_v2.html`](ppt/pitch_v2.html) | 10 分鐘正式舞台版，含 3 分鐘 Demo 與逐頁講者提示 |
| [`../output/pdf/mindfolio-time-machine-proposal-v2.pdf`](../output/pdf/mindfolio-time-machine-proposal-v2.pdf) | 20 頁 16:9 正式繳交 PDF |
| [`../output/pdf/mindfolio-pitch-v2.pdf`](../output/pdf/mindfolio-pitch-v2.pdf) | 10 頁 16:9 舞台版 PDF |

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
- AI 最小改動整合需求：`14_AI_MINIMAL_INTEGRATION_SPEC.md`
- Post-P0 優化候選：`15_OPTIMIZATION_CHECKLIST.md`
