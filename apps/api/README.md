# API App

建議以 FastAPI 實作。API 負責資料查詢、情境卡排序、使用者回饋、Portfolio、事件收集與最小成效指標；不實作通用聊天 Agent。

## 三天版本模組

```text
src/
├── context_builder     # 組合市場、法人、社群與 Portfolio context
├── moment_engine       # 排序今天最值得出現的卡片
├── card_generator      # 產生結構化 Action Card
├── portfolio_service   # 儲存使用者確認結果與 Concern Signal
└── event_service       # 冪等接收互動事件與聚合 MVP metrics
```

## 最小 API

| Method | Path | 用途 |
|---|---|---|
| GET | `/v1/stocks/{stock_id}/context` | 取得指定日期的結構化股票情境 |
| GET | `/v1/users/{user_id}/cards/next` | 取得下一張高價值洞察卡 |
| POST | `/v1/users/{user_id}/cards/{card_id}/feedback` | 接收一鍵回饋 |
| GET | `/v1/users/{user_id}/portfolio` | 取得已確認持股 |
| POST | `/v1/users/{user_id}/concern-feedback` | 接收低門檻提醒偏好 |
| POST | `/v1/events/batch` | 同步前端 event outbox |
| GET | `/v1/users/{user_id}/events` | Demo 事件檢查 |
| GET | `/v1/dashboard/metrics` | 最小漏斗指標 |
| POST | `/v1/users/{user_id}/reset` | 重置該使用者 Demo 狀態（關係、回饋、已生成卡片） |
| GET | `/health` | 服務存活檢查 |

`cards/next` 無卡可出時回 `204 No Content`。完整初版合約見 [`contracts/openapi.yaml`](contracts/openapi.yaml)。

## AI 邊界

- Python 計算數值、趨勢與排序，不把算術交給 LLM。
- Bedrock 將證據轉成可讀敘事及結構化卡片。
- LLM 不決定買賣、不預測股價、不把社群彙總解讀成個人焦慮。
- 三天內不做模型訓練、RAG、向量資料庫或 Agent framework。
