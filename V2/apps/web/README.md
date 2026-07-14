# React frontend

**V2 兩階段（獲客 → 留存）vertical slice 已完成。** React + TypeScript 前端包含：

獲客（Time Machine）:

- `/`：Landing 與 API health 狀態。
- `/builder`：熱門清單、300 檔搜尋與五檔選擇。
- `/reconstruct/:index`：月份 envelope、band／exact 價格、逐筆 validation，
  最後一檔送出五檔 complete。
- `/result`：只顯示後端回傳的人格、報酬、指紋、分數與 AI／fallback
  敘事，並在明確同意後保存仍持有候選。

留存（Portfolio Radar）:

- `/activate`：邀請碼啟用，換取 server-derived session token（demo `demo-leo:LEO`）。
- `/app`：Portfolio Radar dashboard（報告/指紋、持股、priority action card、
  weekly review），由 `features/portfolio-radar/` 提供。

API client 位於 `src/shared/api/client.ts`，以 TypeScript + Zod 驗證回應；
目前是手寫 typed client，尚未導入 OpenAPI codegen。預設 base URL 為
`/api/v2`：本機由 Vite proxy 轉送，正式 Compose 由 nginx proxy 轉送。

啟動與測試見 [`../../DEVELOPMENT.md`](../../DEVELOPMENT.md)，API 合約與資料流
見 [`../../docs/09`](../../docs/09_FRONTEND_BACKEND_ARCHITECTURE.md)。身份由邀請碼
adapter 發出的 session 推導（`LEO` 為 demo identity）；真正的註冊登入系統仍為
roadmap。
