# Mindfolio AI

> 先給洞察，再用一次點擊建立真實庫存情境。

CMoney 籌碼 K 線黑客松原型。Mindfolio AI 不建立另一個 ChatGPT 頁面，也不要求使用者上傳券商截圖或填寫完整資產；它把 AI 嵌入原本的看盤流程，在市場事件值得注意時先顯示有證據的洞察，再用「是我的持股／只是觀察／不相關」取得最低敏感度的一鍵回饋。

## 核心創新

**Reverse Portfolio Onboarding**：傳統產品先索取資料再提供價值；本方案先證明洞察價值，再請使用者確認股票關係。

```text
籌碼 K 線既有使用流程
  → 市場＋法人＋社群資料融合
  → Moment Engine 選出最值得出現的事件
  → Generative Action Card 先呈現洞察
  → LEO 一鍵確認關係
  → 建立使用者已確認的 Portfolio Context
```

## 專案結構

```text
apps/
├── web/                 # React 目標結構與可操作靜態 prototype
└── api/                 # FastAPI 目標結構與 OpenAPI contract
infra/
└── schema/              # PostgreSQL schema
docs/
├── 00...11              # 提案、產品、技術、Demo 與共用 Spec
├── ppt/                 # HTML 簡報初版
└── brainstromingm/      # 未採用的備案，不混入主線
data/                    # 主辦方簡報、workshop 與 CSV package
assets/                  # Demo／Pitch 素材
```

## 快速查看

- Web Prototype：[`apps/web/prototype/index.html`](apps/web/prototype/index.html)
- HTML Slides：[`docs/ppt/index.html`](docs/ppt/index.html)
- 團隊共用 Spec：[`docs/11_COMPLETE_MVP_SPEC.md`](docs/11_COMPLETE_MVP_SPEC.md)
- API Contract：[`apps/api/contracts/openapi.yaml`](apps/api/contracts/openapi.yaml)
- Database Schema：[`infra/schema/001_init.sql`](infra/schema/001_init.sql)

## 資料與聲明

- Demo 資料基準日固定為 `2025-12-31`。
- 官方 package 提供的是個股市場、法人、基本面與社群每日彙總，不含個人持股、不含 user event log、不含貼文原文。
- 「明確多空貼文 93.9% 偏多」只代表可判定方向的貼文比例，不代表個人情緒。
- AI 僅提供資料整理與情境說明，不構成投資建議。
