# Mindfolio Time Machine V2 — End-to-End MVP Spec

## 1. 目標

三天 MVP 驗證單一閉環：

> 陌生使用者不聊天、不上傳截圖、不連券商，只用五檔股票與模糊交易記憶，換取經 2025 行情驗證的投資人格；若自願同意，再把仍持有關係轉成 CMoney 可用的 confirmed holding。

正式 runtime 為 `apps/web` + `apps/api`。`demo/` 只作為視覺、簡報與離線備援 reference，不是金融計算來源。

## 2. 使用者流程

```text
Landing
  → 熱門推薦／搜尋 300 檔
  → 選滿 5 檔
  → 每檔輸入買進月份與價格精度
  → 標記仍持有／已賣出
  → FastAPI 逐筆驗證
  → FastAPI 重建 5 檔結果
  → 人格／報酬／指紋／AI 敘事
  → 匿名分享
  → 明確同意後保存仍持有關係
```

測試 persona 固定使用 `LEO`；正式版必須由登入 session 取得 identity，不得信任 client 傳入任意 user ID。

## 3. 前端範圍

| Route | 責任 | 主要 API |
|---|---|---|
| `/` | 價值主張、零上傳／零聊天入口、API 狀態 | `GET /health` |
| `/builder` | 熱門／搜尋、選滿五檔、顯示可用月份數 | `GET /stocks/popular`, `/stocks/search` |
| `/reconstruct/:index` | 逐檔月份、區間／精確價格、持有關係 | `GET /envelope`, `POST /validate`, `POST /complete` |
| `/result` | 只呈現後端 result、人格卡、同意保存 | `POST /confirmed-holdings` |

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

### 持股同意

- 僅 `relation=holding` 的候選可寫入。
- 後端重跑 reconstruction 後才 persistence。
- MVP 只存 `user_id`, `stock_id`, `source`, `confirmed_at`。
- 不存買價、賣價、報酬與人格明細。

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
- 遵守 schema 與禁語 guardrail。
- provider 失敗時回 deterministic fallback。

AI 不做：

- 股價、報酬、人格或持股候選計算。
- 投資買賣建議、目標價或報酬保證。
- 從未驗證輸入直接生成金融結論。

## 7. 架構取捨

| 決策 | 優點 | 缺點／後續 |
|---|---|---|
| React reducer/context | 零額外依賴、跨 route 夠用 | refresh 會失去匿名 draft；正式版改 server session |
| Zod typed client | runtime 可攔 contract drift | 手寫 schema 有維護成本；CI 後續改 OpenAPI codegen |
| JSON market snapshot | 快、可重現、無 DB 查詢成本 | 不適合即時更新；live feed 另建 adapter |
| Sync FastAPI services | 邏輯簡單、deterministic 計算可預測 | Bedrock 高延遲時需 async／worker |
| PostgreSQL 只存 confirmed holdings | 隱私與 schema 最小化 | 無法跨裝置續填；正式版增加 reconstruction session |

## 8. 驗收條件

- [x] 使用者可搜尋並選擇五檔 2025 股票。
- [x] 前端只顯示該股票真正有資料的月份。
- [x] 每檔可用 band 或 exact，且公司行動規則由 API 決定。
- [x] complete 的人格、報酬、分數、指紋全部來自 FastAPI。
- [x] Bedrock 關閉或失敗時仍有 deterministic narrative。
- [x] 使用者未勾同意時不可保存 confirmed holdings。
- [x] React production build 與 Python test suite 通過。
- [ ] 正式身份驗證、rate limit、event analytics、Docker／AWS 部署。

## 9. 模組路徑

- React routes：`V2/apps/web/src/routes/`
- Wizard state：`V2/apps/web/src/features/reconstruction/ReconstructionContext.tsx`
- Typed API client：`V2/apps/web/src/shared/api/client.ts`
- FastAPI routers：`V2/apps/api/src/mindfolio_api/routers/`
- Deterministic service：`V2/apps/api/src/mindfolio_api/services/reconstruction.py`
- Core calculation：`V2/packages/mindfolio-core/src/mindfolio_core/market/`
- PostgreSQL schema：`V2/infra/schema/001_init.sql`
