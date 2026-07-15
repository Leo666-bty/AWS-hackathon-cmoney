# CMoney Hackathon — Mindfolio Versions

本工作區用版本資料夾保存兩次產品方向，避免舊概念與新 Demo 混在一起。

## Active version

### [V2 — 2025 投資時光機 × 投資人格實驗室](V2/README.md)

使用者從熱門推薦或 300 檔資料庫自選五檔，以月份與價格區間重建買進、賣出或持有狀態，立即取得：

- 經月份行情驗證與公司行動調整的五檔等權重推估報酬。
- 四軸投資人格與可分享結果卡。
- Portfolio Fingerprint、資料可信度與「2025 情境決策力」拆解。
- 從匿名測驗、分享、註冊、補充持股到持續監測的成長漏斗。

快速入口：

- [V2 本機啟動（正式 React + FastAPI 產品）](V2/DEVELOPMENT.md)
- [V2 靜態 UX 參考](V2/demo/index.html)（早期 HTML/JS mockup，非後端串接的正式產品）
- [V2 文件中心](V2/docs/README.md)
- [版本變更與心路歷程](CHANGELOG.md)

## Archived version

### [V1 — Reverse Portfolio Onboarding](V1/README.md)

原始 Mindfolio AI 方案完整封存於 `V1/`，包含舊 Demo、文件、AI training、API contract、資料包、簡報，以及遠端新增的 SpecKit／Claude workflow 與 API SDD。V1 不再作為目前提案來源，但可用於追溯「先提供洞察，再取得持股確認」的設計脈絡。

## Version rule

- 根目錄只放跨版本說明與共用排除規則。
- 新提案內容只更新 `V2/`。
- `V1/` 僅封存，不再同步修改。
- 主辦方原始資料存放於 `V2/data/`（active version 自帶資料，gitignored 不進 remote）；V1 只封存當時的文件與 demo。
