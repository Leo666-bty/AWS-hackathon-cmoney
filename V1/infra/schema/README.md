# Database Schema

[`001_init.sql`](001_init.sql) 保存三天 MVP 的必要狀態：

- 使用者與股票
- 已確認 Portfolio Relationship
- Action Card 與一鍵回饋
- Concern Signal
- 冪等互動事件
- 清楚標示的 Demo News

`average_cost` 與 `shares` 只保留 nullable 擴充欄位，首次互動不收集。刻意不保存券商帳號、截圖、完整資產與自由聊天紀錄。
