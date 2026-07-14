# Product & UX

## 體驗流程

```text
Landing
→ 熱門推薦／300 檔搜尋
→ 選滿五檔
→ 買進月份
→ 價格區間或實際價格
→ 逐檔設定仍持有或已賣出
→ 若已賣出，設定賣出月份與估算／實際價格
→ Reconstruction Engine
→ 人格、報酬、可信度、持股確認
→ 匿名分享
→ 註冊保存與持股雷達
```

## Step 1：五檔選股

- 預設顯示同學會瀏覽人數前 12 名。
- 搜尋支援代號、名稱、產業。
- 「使用熱門五檔體驗」是 Demo shortcut，不應取代真實選股。
- 選滿五檔才可繼續。

## Step 2：逐檔重建

每檔詢問：

1. 2025 買進月份。
2. 月內偏低／中間／偏高區，或實際成交價。
3. 2025-12-31 是否仍持有。
4. 若已賣出，再問賣出月份與估算／實際價格。

手動價格超出該月原始高低價時阻擋下一步，提示使用者修正月份、價格或改用區間。這只能提高資料品質，不能當作成交證明。

正式版每次股票搜尋與價格檢查都呼叫 FastAPI。前端可以暫存尚未送出的欄位，但 validation message、allowed price mode 與 company-action state 以後端 response 為準。

## Step 3：結果

首屏 Output：

- 投資人格四字母代碼。
- 五檔等權重推估報酬。
- 資料重建可信度。
- 主動確認仍持有的股票數。

下方依序顯示：

- 五檔買賣 Timeline。
- AI narrative 與 deterministic fallback 說明。
- 匿名人格分享卡。
- Portfolio Fingerprint vector 與情境決策力拆解。
- 明確 consent 後保存 `LEO` confirmed holdings 的 CTA。

Result 必須完全使用 FastAPI `reconstructions/complete` response；前端不可自行重算數字或在 API 失敗時產生未驗證人格。

現行 MVP 尚無登入、報告認領或 Portfolio Radar route；這些屬下一階段
Progressive Profiling 規格，不可在 Demo 中描述為已完成。

## Progressive Profiling（產品路線圖）

| 階段 | 使用者提供 | 系統回饋 |
|---|---|---|
| 匿名選股 | 五檔股票 | 可玩的個人題目 |
| 月份／價格 | 模糊或精確交易記憶 | 報酬重建、人格、可信度 |
| 仍持有確認 | 股票關係 | Portfolio 與個人雷達 |
| 註冊同意 | 身份與保存授權 | 跨裝置報告、持續追蹤 |

## 隱私

分享卡預設不包含股票、月份、價格、報酬明細與 confirmed holding。現行 wizard
只存在 React 記憶體，重新整理即清空；尚未實作 localStorage、匿名 event 或報告
持久化。正式上線需加入身份、保存期限、同意、刪除與撤回機制。
