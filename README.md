# Mindfolio AI

> 先給洞察，再用一次點擊建立真實庫存情境。

CMoney 籌碼 K 線黑客松三天 MVP。Mindfolio AI 不建立另一個 ChatGPT 頁面，也不要求使用者上傳券商截圖或填寫完整資產；它把 AI 嵌入原本的看盤流程，在市場事件值得注意時先顯示有證據的洞察，再用「是我的持股／只是觀察／不相關」取得最低敏感度的一鍵回饋。

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
├── web/                 # React 目標結構與可操作 MVP reference
├── api/                 # FastAPI 實作邊界與 OpenAPI contract
└── ai-training/         # Python 離線 Market Moment Detector
infra/
└── schema/              # PostgreSQL schema
docs/
├── 00...11              # 提案、產品、技術、Demo 與共用 Spec（給人讀的專案碎片）
├── api/                 # 後端各功能的 SDD 規格（001 核心迴圈、002 事件/儀表板）
├── ppt/                 # HTML 簡報初版
└── brainstromingm/      # 未採用的備案，不混入主線
data/                    # 主辦方簡報、workshop 與 CSV package
assets/                  # Demo／Pitch 素材
.specify/                # Spec Kit 工具設定：憲法、範本、腳本（工具維護，勿手改）
.claude/skills/          # /speckit-* 指令本體
```

## 文件結構與 Spec-Driven Development

後端採用 Spec-Driven Development（GitHub Spec Kit）。三個資料夾分工，一句話記住：**規格改 `docs/`，工具設定別碰 `.specify/`。**

| 位置 | 是什麼 | 誰用 |
|---|---|---|
| `docs/` | 給人讀的文件。`docs/00~11` 是專案共識碎片；`docs/api/<NNN-feature>/` 是各功能的規格（`spec` 需求 → `plan` 技術計畫 → `tasks` 任務拆解） | 人打開讀、討論、提需求 |
| `.specify/` | Spec Kit 工具的設定與範本（規則、腳本）。裡面唯一值得人讀的是 `.specify/memory/constitution.md`——專案的工程鐵律 | 工具維護，勿手動改 |
| `.claude/skills/` | 在 Claude Code 裡打的 `/speckit-*` 指令 | 工具用 |

打個比方：`.specify/` 是模具與規則手冊，`docs/api/` 是壓出來的成品。功能規格看 `docs/api/`；`docs/00~11` 若與規格衝突，以 `docs/11_COMPLETE_MVP_SPEC.md` 為準。

SDD 流程：`/speckit-specify`（寫規格）→ `/speckit-clarify`（問清楚）→ `/speckit-plan`（技術計畫）→ `/speckit-tasks`（拆任務）→ `/speckit-implement`（實作）。

## 快速查看

- Interactive MVP Reference：[`apps/web/prototype/index.html`](apps/web/prototype/index.html)
- HTML Slides：[`docs/ppt/index.html`](docs/ppt/index.html)
- 團隊共用 Spec：[`docs/11_COMPLETE_MVP_SPEC.md`](docs/11_COMPLETE_MVP_SPEC.md)
- API Contract：[`apps/api/contracts/openapi.yaml`](apps/api/contracts/openapi.yaml)
- AI Training：[`apps/ai-training/README.md`](apps/ai-training/README.md)
- Database Schema：[`infra/schema/001_init.sql`](infra/schema/001_init.sql)

## 資料與聲明

- Demo 資料基準日固定為 `2025-12-31`。
- 官方 package 提供的是個股市場、法人、基本面與社群每日彙總，不含個人持股、不含 user event log、不含貼文原文。
- 「明確多空貼文 93.9% 偏多」只代表可判定方向的貼文比例，不代表個人情緒。
- AI 僅提供資料整理與情境說明，不構成投資建議。
- 新聞頁目前是明確標示的 Demo Feed；正式部署必須改接有授權來源。
- 使用者互動先寫入瀏覽器 outbox；接上 `/api/v1/events/batch` 後才標示為已同步。
