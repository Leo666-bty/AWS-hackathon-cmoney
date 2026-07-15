# Mindfolio Time Machine V2 — End-to-End MVP Spec

## 1. 目標

三天 MVP 驗證單一閉環：

> 陌生使用者不聊天、不上傳截圖、不連券商，只用五檔股票與模糊交易記憶，換取經 2025 行情驗證的投資人格；若自願同意，再把仍持有關係轉成 CMoney 可用的 confirmed holding。

正式 runtime 為 `apps/web` + `apps/api`。`demo/` 只作為 presentation-only 的
視覺／簡報 reference，不是 runtime fallback 或正式金融計算來源。

## 2. 使用者流程

```text
Landing
  → 熱門推薦／搜尋 300 檔
  → 選滿 5 檔
  → 每檔輸入買進月份與價格精度
  → 標記仍持有／已賣出
  → FastAPI 逐筆驗證
  → FastAPI 重建 5 檔結果（回傳 report handle）
  → 人格／報酬／指紋／AI 敘事
  → 匿名分享
  --- 留存（Portfolio Radar）---
  → /activate 邀請碼換 session token
  → 認領報告（POST /reports/{id}/claim）
  → 明確同意後 report-scoped 保存仍持有關係
  → /app Portfolio Radar（dashboard／card／weekly review）
```

身份由邀請碼 adapter 發出的 server-derived session 推導（demo `demo-leo:LEO`
映射到 `LEO`）；留存端點一律不信任 client 傳入的 user ID。

## 3. 前端範圍

| Route | 責任 | 主要 API |
|---|---|---|
| `/` | 價值主張、零上傳／零聊天入口、API 狀態 | `GET /health` |
| `/builder` | 熱門／搜尋、選滿五檔、顯示可用月份數 | `GET /stocks/popular`, `/stocks/search` |
| `/reconstruct/:index` | 逐檔月份、區間／精確價格、持有關係 | `GET /envelope`, `POST /validate`, `POST /complete` |
| `/result` | 只呈現後端 result、人格卡、匿名分享 | `POST /complete`（含 report handle）|
| `/activate` | 邀請碼啟用、換取 session token | `POST /auth/session` |
| `/app` | Portfolio Radar：dashboard、認領、持股授權、卡片回饋 | `POST /reports/{id}/claim`, `POST /reports/{id}/confirmed-holdings`, `GET /me/dashboard`, `POST /me/action-cards/{id}/feedback` |

前端可保存 wizard draft，不可計算正式報酬、調整因子、人格、分數或持股候選。

## 4. API 契約

Base path：`/api/v2`。OpenAPI：`/api/v2/openapi.json`。

### 股票摘要

`StockSummary` 必須包含：

```json
{
  "id": "2330",
  "name": "台積電",
  "industry": "半導體",
  "views": 253191,
  "popular": true,
  "available_months": ["01", "02", "03"]
}
```

`available_months` 是正式 UI contract，避免新上市或缺月股票靠 404 猜測可選月份。

### 重建

- 每次 complete 必須剛好五筆。
- FastAPI 必須重新驗證，不信任先前 validate response。
- 公司行動月若不允許 band，前端切換 exact；後端仍是最終裁決者。
- complete response 是 UI 唯一金融真相。

### 持股同意（report-scoped，session 驗證）

- 唯一寫入路徑為 `POST /reports/{report_id}/claim` 認領後的
  `POST /reports/{report_id}/confirmed-holdings`。
- 僅屬於該報告 `holding_candidates` 的候選可寫入（否則 422）。
- 後端由已認領報告的原始 trades 重跑 reconstruction 後才 persistence。
- 存 `user_id`、`stock_id`、`source`、`confirmed_at`，並記錄 `source_report_id`
  與 `last_reviewed_at`；不存買價、賣價、報酬與人格明細。

> 已移除（安全性）：舊的未驗證 `POST /confirmed-holdings` 與
> `GET /users/{user_id}/confirmed-holdings`（信任 client `user_id` 的跨會員隔離
> 漏洞）已刪除。

### 留存端點（Portfolio Radar，6 支）

- `POST /auth/session`：邀請碼 → `{access_token, member_id, display_name}`；無效碼 401。
- `POST /reports/{report_id}/claim`：綁定報告到 session 會員；404／403／410／409／503。
- `POST /reports/{report_id}/confirmed-holdings`：唯一確認持股寫入路徑（見上）。
- `GET /me/dashboard`：`{member_id, display_name, report, portfolio, priority_card, weekly_review}`。
- `POST /me/action-cards/{card_id}/feedback`：`{preference: review_evidence|routine|mute}`；
  `mute` 目前僅被記錄，尚未改變下一張卡片排序（Feature 006）。
- `POST /events/batch`：以 `event_id` idempotent 寫入互動事件。

## 5. 資料策略：2025 與即時行情

### MVP 採 2025 封存資料

V2 是「2025 投資時光機」，因此重建結果必須鎖定同一資料截點 `asOf=2025-12-31`。優點是結果可重現、Demo 穩定、公司行動可驗證；缺點是不能回答今天盤中狀況。

### 即時資料不混入重建

未來若串接籌碼 K 線即時／盤後資料，應新增獨立 `Live Context API`，只用於結果後的持股雷達、事件卡與回訪，不得改寫既有 2025 reconstruction：

```text
2025 Market Snapshot → Reconstruction Engine → immutable report
Live Market Feed      → Moment Engine         → current context card
```

這個切分避免「同一份人格今天重算後數字改變」，也讓歷史產品與即時陪伴能獨立部署、快取與回滾。

## 6. AI 邊界

AI 的工作：

- 把 verified `ReconstructionResult` 轉成繁體中文敘事。
- 結合離線預先評分的買進月份市場情境，產生結構化 AI Deep Dive。
- 只回答三個 server-defined 證據型問題 ID，不提供自由聊天。
- 遵守 schema 與禁語 guardrail。
- provider 失敗時回 deterministic fallback。

AI 不做：

- 股價、報酬、人格或持股候選計算。
- 投資買賣建議、目標價或報酬保證。
- 從未驗證輸入直接生成金融結論。
- 在 API request 內執行 sklearn inference 或 training。

## 7. 架構取捨

| 決策 | 優點 | 缺點／後續 |
|---|---|---|
| React reducer/context | 零額外依賴、跨 route 夠用 | refresh 會失去匿名 draft；正式版改 server session |
| Zod typed client | runtime 可攔 contract drift | 手寫 schema 有維護成本；CI 後續改 OpenAPI codegen |
| JSON market snapshot | 快、可重現、無 DB 查詢成本 | 不適合即時更新；live feed 另建 adapter |
| Sync FastAPI + pre-scored JSON | 邏輯簡單、O(1) 查表且 production 不需 sklearn | 新資料需重新發布 artifact |
| PostgreSQL 四表（holdings + reports + feedback + events）| 支援報告認領、AI report cache、卡片偏好與 event | 獲客 wizard draft 仍在瀏覽器；真正註冊登入待補 |

## 8. 驗收條件

- [x] 使用者可搜尋並選擇五檔 2025 股票。
- [x] 前端只顯示該股票真正有資料的月份。
- [x] 每檔可用 band 或 exact，且公司行動規則由 API 決定。
- [x] complete 的人格、報酬、分數、指紋全部來自 FastAPI。
- [x] Bedrock 關閉或失敗時仍有 deterministic narrative。
- [x] 使用者未勾同意時不可保存 confirmed holdings。
- [x] 邀請碼可換取 session token；留存端點以 session 推導身份，不信任 client user ID。
- [x] `complete` 回傳 report handle，登入後可認領並綁定會員身份。
- [x] confirmed holdings 只能經 session-authenticated、report-scoped 路徑寫入（舊未驗證端點已移除）。
- [x] `GET /me/dashboard` 回傳 report／portfolio／priority card／weekly review。
- [x] `POST /events/batch` 以 `event_id` idempotent 寫入。
- [x] 結構化 AI Deep Dive、固定問題 ID、ownership、cache 與 fallback 完成。
- [x] React production build、ESLint、React 6 tests 與 Python 67 tests 通過。
- [x] 單一 EC2 用 Docker Compose 定義（web + api + PostgreSQL）與本機容器驗收。
- [ ] HTTPS／自訂網域驗收、真正註冊登入、rate limit 與 event analytics。
- [x] 真實 Bedrock 上線驗證：已於 EC2 實測 live（Converse + 短期 API key），任何失敗仍走 deterministic fallback。
- [ ] 正式 IAM Role 授權、action card `mute` 影響排序（Feature 006）、`docs/api/004..007` SDD 資料夾補齊。

## 9. 模組路徑

- React routes：`V2/apps/web/src/routes/`（含 `ActivateRoute.tsx`、`PortfolioRadarRoute.tsx`）
- Wizard state：`V2/apps/web/src/features/reconstruction/ReconstructionContext.tsx`
- Portfolio Radar modules：`V2/apps/web/src/features/portfolio-radar/`
- Typed API client：`V2/apps/web/src/shared/api/client.ts`
- FastAPI routers：`V2/apps/api/src/mindfolio_api/routers/`（含 `retention.py`）
- Session/identity：`V2/apps/api/src/mindfolio_api/auth.py`
- Deterministic service：`V2/apps/api/src/mindfolio_api/services/reconstruction.py`
- Retention service：`V2/apps/api/src/mindfolio_api/services/retention.py`
- Core calculation：`V2/packages/mindfolio-core/src/mindfolio_core/market/`
- PostgreSQL schema：`V2/infra/schema/001_init.sql`（四表）
