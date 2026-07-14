# Infrastructure

三天版本採最小部署：Web、API、PostgreSQL 三個責任邊界。`schema/` 保存資料結構，不在黑客松內建立複雜 IaC、訊息佇列或向量資料庫。

```text
Web (React)
  → API (FastAPI)
    → PostgreSQL
    → Amazon Bedrock
    → CMoney CSV adapter
```

正式 AWS 部署可使用 Amplify/S3+CloudFront、Lambda 或 App Runner、RDS PostgreSQL；黑客松期間依團隊現有帳號與部署速度擇一，不把雲端服務數量當成完成度。
