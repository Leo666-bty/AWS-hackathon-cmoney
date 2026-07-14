# Technical Architecture

## 最小架構

```text
React Web（籌碼 K 線情境頁）
  → FastAPI
    ├── CSV Adapter
    ├── Context Builder
    ├── Moment Engine
    ├── Bedrock Card Generator
    └── Portfolio Service
  → PostgreSQL
```

## Apps

### `apps/web`

- 個股市場資料
- Generative Action Card
- 一鍵回饋
- 我的庫存情境
- Prototype 先以原生 HTML/CSS/JS 驗證流程，正式版再轉 React

### `apps/api`

- 查詢股票 context
- 排序下一張卡
- 接受一鍵回饋
- 更新已確認 Portfolio
- 對 Bedrock 做 schema validation 與 fallback

## Infra

`infra/schema/001_init.sql` 保存：

- users
- stocks
- portfolio_relationships
- action_cards
- card_feedback

不保存券商資料、截圖、聊天紀錄或完整資產。

## API Contract

以 `apps/api/contracts/openapi.yaml` 為準。前後端不得各自發明欄位。

## AWS 對應

| 能力 | 黑客松選項 |
|---|---|
| Web | Amplify 或 S3 + CloudFront |
| API | Lambda + API Gateway，或 App Runner |
| Database | RDS PostgreSQL；若部署太慢可用既有託管 PostgreSQL |
| GenAI | Amazon Bedrock |
| CSV | S3 或 API 啟動時載入 demo subset |

## 降級策略

1. Bedrock 不可用：使用固定卡片文案，完整互動仍可 Demo。
2. Database 不可用：LEO 狀態暫存在瀏覽器。
3. API 不可用：Prototype 使用內建 2382 evidence JSON。

降級後仍必須完成「洞察 → 一鍵確認 → Portfolio 更新」。
