# React frontend

**V2 acquisition vertical slice 已完成。** React + TypeScript 前端包含：

- `/`：Landing 與 API health 狀態。
- `/builder`：熱門清單、300 檔搜尋與五檔選擇。
- `/reconstruct/:index`：月份 envelope、band／exact 價格、逐筆 validation，
  最後一檔送出五檔 complete。
- `/result`：只顯示後端回傳的人格、報酬、指紋、分數與 AI／fallback
  敘事，並在明確同意後保存 `LEO` 的仍持有候選。

API client 位於 `src/shared/api/client.ts`，以 TypeScript + Zod 驗證回應；
目前是手寫 typed client，尚未導入 OpenAPI codegen。預設 base URL 為
`/api/v2`：本機由 Vite proxy 轉送，正式 Compose 由 nginx proxy 轉送。

啟動與測試見 [`../../DEVELOPMENT.md`](../../DEVELOPMENT.md)，API 合約與資料流
見 [`../../docs/09`](../../docs/09_FRONTEND_BACKEND_ARCHITECTURE.md)。正式身份、
註冊認領與 Portfolio Radar 尚未實作；`LEO` 僅為 Demo identity。
