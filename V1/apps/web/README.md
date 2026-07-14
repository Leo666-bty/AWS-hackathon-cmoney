# Web App

Mindfolio AI 的 React 目標應用與可操作 MVP reference，嵌入籌碼 K 線既有研究流程，不是獨立聊天頁。

## MVP Pages

| Page | Responsibility |
|---|---|
| 自選股 | 正常研究入口與 `stock_open` |
| 個股 | 即時、盤後、社群、新聞與 AI 情境卡 |
| 我的庫存 | 已確認關係、Concern Signal、移除持股 |
| 營運 Dashboard | 四個最小指標、最近事件與同步狀態 |

## Interaction Rules

- 一鍵回饋：是我的持股／只是觀察／不相關。
- AI 追問使用預設問題，不提供空白 ChatGPT 輸入框。
- Concern 只收 `worried/routine/mute`，不生成焦慮分數。
- localStorage 分開保存 demo state、event history 與 pending outbox。
- API 成功前事件只顯示 `queued`，不可假裝已同步。

## Run Reference

直接開啟 [`prototype/index.html`](prototype/index.html)。正式三天 MVP 應以 React 串接 OpenAPI；此 reference 同時作為 UI contract 與斷網備援。

新聞目前是清楚標示的 Demo Feed，正式產品必須改接有授權來源。
