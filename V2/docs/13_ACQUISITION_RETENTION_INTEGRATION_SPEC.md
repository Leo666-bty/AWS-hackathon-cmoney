# Mindfolio 獲客至留存整合需求規格

**文件編號**：`MF-RET-001`

**建立日期**：2026-07-14

**狀態**：P0 會員介面與留存閉環已完成 — 2026-07-15

**主要實作根目錄**：`V2/`

**參考來源**：已封存的 `V1/` 產品概念與契約

**依賴文件**：`12_V2_END_TO_END_SPEC.md`、`api/003-confirmed-holdings/spec.md`

## 1. 決策與目的

Mindfolio 是同一個產品，包含前後相接的兩個生命週期階段：

```text
Time Machine 獲客體驗（目前 V2）
→ 匿名投資重建與立即價值
→ 註冊／認領報告／明確持股授權
→ Portfolio Radar 留存體驗（選用 V1 能力）
→ 週期性證據、回饋與回訪
```

目前 `V2/` 仍是唯一有效的實作根目錄。本規格**不授權**將 `V1/` 恢復為第二套應用、不允許直接複製其完整執行環境，也不維護兩套 API 版本。V1 僅作為產品與領域參考；選定的留存需求必須重新規格化，以符合 V2 的 React + FastAPI 架構。

本文件是後續 SDD 工作的需求基準。每個交付切片在進入實作前，都必須產出自己的 `spec.md`、`plan.md`、`tasks.md`、OpenAPI 變更、Schema Migration 與驗收追蹤。

## 2. 問題定義

目前 Time Machine 已驗證匿名獲客流程：

- 陌生使用者可選擇五檔熟悉的股票；
- FastAPI 會驗證月份與價格輸入；
- 重建引擎會回傳投資組合結果、可信度與人格；
- 使用者可分享匿名人格圖卡；
- 經明確標示的持股可在使用者同意後保存。

若旅程停在結果頁，Mindfolio 仍只是一個一次性活動。系統缺少讓使用者註冊、回訪並逐步改善 Portfolio 資料的長期理由。留存階段必須把已認領的 Time Machine 報告與已確認持股，轉換成可持續回訪的 Portfolio Radar，同時不得削弱獲客流程，也不得把推測興趣當成真實持股。

## 3. 產品邊界與名詞

| 名詞 | 在目前 V2 產品中的定義 |
|---|---|
| Time Machine | 匿名獲客介面：五檔股票重建、人格、報告與分享圖卡 |
| 會員啟用（Member Activation） | 使用者完成身份驗證或建立帳號，並認領匿名報告的明確轉換階段 |
| Portfolio Radar | 會員留存介面：已確認持股、優先市場時刻與週期性回顧 |
| 重建候選（Reconstruction Candidate） | 測驗中選取的股票；本身不代表持股 |
| 已確認持股（Confirmed Holding） | 使用者明確同意，且經後端重新驗證的持股關係 |
| 市場時刻（Market Moment） | 由確定性規則或模型協助產生，值得使用者注意的證據組合 |
| 行動卡（Action Card） | 根據已驗證 Market Moment DTO 產生的會員端說明卡片 |
| 關注偏好（Concern Preference） | 使用者明確設定的提醒偏好，例如 `routine` 或 `mute`；不可當成推測的心理狀態 |

對外產品與提案語言應使用 **Time Machine** 與 **Portfolio Radar**。`V1` 和 `V2` 僅是儲存庫歷史標籤。

## 4. 目標與成功標準

### 4.1 目標

1. 保留 V2 低門檻的匿名獲客體驗。
2. 讓結果頁的註冊 CTA 提供明確會員價值交換。
3. 允許會員跨裝置認領不可變更的 2025 年報告。
4. 只有經使用者明確同意的候選，才能轉成已確認持股。
5. 使用已確認持股選擇具證據依據的 Action Card。
6. 提供支援週期性回訪的精簡會員首頁。
7. 收集明確回饋與互動事件，供未來排序模型使用。
8. 重用 V1 的產品經驗，但不建立平行的 V1 執行環境。

### 4.2 產品成效指標

| 階段 | 主要指標 | 輔助指標 |
|---|---|---|
| 獲客 | 重建完成率 | 開始率、取得結果時間、驗證修正率 |
| 推薦傳播 | 匿名圖卡分享率 | 分享點擊、下載、推薦流量 Session |
| 啟用 | 報告認領率 | 註冊 CTA 點擊率、認領完成率 |
| Portfolio 啟用 | 已驗證持股啟用數 | 授權率、每位啟用會員的確認持股數 |
| 留存 | D7／D30 Portfolio Radar 回訪率 | Action Card 開啟、證據展開、週報開啟 |
| 資料品質 | 明確關係覆蓋率 | 修正、移除、靜音與過期持股複核率 |

Demo Session 只能證明事件量測與端到端狀態轉移成立，不得宣稱為已達成的市場轉換率。

## 5. 端到端使用者旅程

### 5.1 匿名獲客

```text
Landing
→ 選擇五檔股票
→ 重建五筆交易
→ 取得不可變更的 2025 年報告
→ 查看人格圖卡、雷達與 AI 敘事
→ 匿名分享，或選擇「保存報告並開啟 Portfolio Radar」
```

使用者取得核心結果前，不需要登入。

### 5.2 會員啟用

```text
結果頁 CTA
→ 驗證身份／建立帳號
→ 認領匿名重建報告
→ 檢視「仍持有」候選
→ 提供明確授權
→ 後端重新驗證候選
→ 建立已確認持股
→ 進入 Portfolio Radar
```

身份驗證失敗或使用者取消時，不得刪除匿名報告，也不得錯誤標記為已認領。

### 5.3 留存循環

```text
會員開啟 Portfolio Radar
→ 查看目前 Portfolio 快照
→ 開啟最高優先級 Action Card
→ 檢視確定性證據與資料日期
→ 提交關係／提醒偏好回饋
→ 系統記錄冪等事件
→ 後續卡片與每週回顧反映明確偏好
```

2025 年歷史重建與目前市場情境是兩種獨立資料產品。即時情境不得默默改寫不可變更的 Time Machine 報告。

## 6. 資訊架構

### 6.1 必要介面

| 路由／介面 | 對象 | 責任 | 交付優先級 |
|---|---|---|---|
| `/result` | 匿名使用者 | 既有報告、分享、會員價值預覽與啟用 CTA | P0 既有功能＋文案調整 |
| `/activate` | 匿名 → 會員 | 身份驗證銜接、報告認領與持股授權檢視 | P0 |
| `/app` | 會員 | Portfolio Radar 首頁：投資指紋、Portfolio、優先卡片與每週回顧 | P0 |
| `/app/portfolio` | 會員 | 已確認關係、完整度、修正與移除 | P1 |
| `/app/stocks/:stockId` | 會員 | 已確認或僅觀察股票的證據詳情 | P1 |
| 內部漏斗頁 | 內部 Demo／營運人員 | 驗證事件、啟用數與持股數 | P2 |

黑客松 P0 可將 `/app` 實作為單一路由搭配可展開區塊，不要求完整的多頁會員應用。

### 6.2 Portfolio Radar 首頁需求

P0 會員首頁必須包含四個模組：

1. **Portfolio Fingerprint**：已認領人格、四軸分數、報告日期與重建可信度。
2. **Confirmed Portfolio**：只顯示已確認持股，包含來源與最後確認時間；缺少股數與成本時必須明確顯示未知。
3. **Priority Action Card**：針對已確認持股提供一張有證據依據的市場時刻卡，包含資料日期、證據與降級狀態。
4. **Weekly Review Preview**：Portfolio 事件與下一次價值交換的精簡摘要；Demo 可使用 Fixture 或目前快照資料，但必須清楚標示。

P0 實作採單一路由與獨立區塊導覽，四個模組不可混成線性教學流程。介面必須補足下列可驗證狀態：

- 四軸分數使用中文名稱，並提供可被輔助工具辨識的數值語意；
- 每筆持股清楚顯示本人確認來源、複核日期，以及股數／成本未知狀態；
- Action Card 顯示資料日期、證據來源與 `Bedrock 生成`／`規則備援` 狀態；
- 情境式 Follow-up 使用有限選項，回答只能由現有證據決定，不提供自由投資問答；
- Weekly Review 明確標示目前快照或 Demo Fixture，不暗示已完成排程與即時資料能力；
- Feedback、載入與錯誤狀態必須有可見訊息，且重要更新使用 `aria-live` 或等效無障礙語意。

## 7. 功能需求

### 7.1 會員啟用與報告認領

- **FR-ACT-001**：匿名重建完成時，系統必須簽發不透明的重建／報告 ID；不得只憑前端計算的人格或結果值建立認領。
- **FR-ACT-002**：會員成功啟用時，後端必須將報告 ID 綁定至已驗證會員，且操作必須具備冪等性。
- **FR-ACT-003**：已由其他會員認領的報告不得再次認領；API 必須回傳衝突，但不得洩漏另一位會員身份。
- **FR-ACT-004**：目前寫死的 `LEO` 身份僅供 Demo。留存 SDD 必須以伺服器端驗證身份或明確的 Demo Identity Adapter，取代前端任意傳入的 User ID。
- **FR-ACT-005**：認領報告不得自動建立持股。持股授權必須是另一個獨立且明確的操作。
- **FR-ACT-006**：已認領的 2025 年重建結果必須維持不可變更；後續市場資料可以增加情境，但不得修改歷史數字。
- **FR-ACT-007**：取消啟用或身份供應者失敗時，匿名報告在設定期限內仍必須可讀，且不得記錄成功啟用事件。

### 7.2 已確認 Portfolio

- **FR-POR-001**：只有標記為 `relation=holding`、在授權階段經使用者明確選取，且由 FastAPI 成功重新驗證的候選，才能成為已確認持股。
- **FR-POR-002**：搜尋、瀏覽頁面、分享、重建選股與模型推論都不得建立已確認持股。
- **FR-POR-003**：每筆關係必須記錄會員 ID、股票 ID、類型、`source=user_confirmed`、來源報告 ID、確認時間與最近複核時間。
- **FR-POR-004**：股數、平均成本與券商必須保持 nullable 且選填；首次啟用不得強制要求。
- **FR-POR-005**：會員必須能將關係修正為 `watch_only` 或移除。最新明確回覆優先，但先前狀態必須可稽核。
- **FR-POR-006**：Portfolio UI 必須區分已確認、僅觀察與待複核關係，且不得把候選標示成持股。

### 7.3 Market Moment 與 Action Card

- **FR-MOM-001**：Action Card 候選必須來自經驗證的市場、法人、估值或社群彙總證據，並包含 `as_of` 日期與來源 Key。
- **FR-MOM-002**：AI 產生敘事之前，候選排序必須具確定性且可檢查。基準公式為 `relevance × impact × novelty − interruption_cost`。
- **FR-MOM-003**：已確認持股可提高關聯性；`watch_only`、`irrelevant` 與 `mute` 回饋必須依文件化規則改變優先級。
- **FR-MOM-004**：Market Regime 或異常模型結果可以補充市場時刻，但必須包含模型版本、特徵版本與證據提示。
- **FR-MOM-005**：原始異常分數不得呈現為預測準確率或買賣訊號。UI 應使用可理解的等級與證據。
- **FR-MOM-006**：模型產物不可用或版本不相容時，服務必須降級使用確定性證據，不得阻擋會員首頁。
- **FR-MOM-007**：P0 會員首頁最多需要一張優先卡，不要求完整 Feed 或通知排程器。

### 7.4 Bedrock 敘事

- **FR-AI-001**：Bedrock 只能接收已驗證 DTO；不得計算報酬、指定持股、修改模型分類或查詢憑證。
- **FR-AI-002**：AI 輸出在顯示前必須通過型別 Schema 與禁用語句檢查。
- **FR-AI-003**：供應者逾時、拒絕、Schema 無效或 AWS 憑證不可用時，必須回傳具有相同數值證據的確定性降級卡片。
- **FR-AI-004**：輸出不得包含買賣方向、目標價、獲利保證、心理診斷，或宣稱社群彙總代表會員個人情緒。
- **FR-AI-005**：UI 必須顯示證據日期與 fallback／generated 來源狀態，不得把 LLM 描述為金融事實來源。

### 7.5 回饋、偏好與事件

- **FR-EVT-001**：系統必須以型別化事件記錄啟用、報告認領、Portfolio 查看、卡片曝光、證據展開、關係回饋、提醒偏好與持股移除。
- **FR-EVT-002**：前端事件必須使用穩定 Event ID，批次寫入必須冪等；重試不得增加指標計數。
- **FR-EVT-003**：事件是行為訊號，不是持股事實。只有明確的關係回饋可以更新 Portfolio Relationship。
- **FR-EVT-004**：`routine`、`mute` 等提醒回饋必須描述為內容偏好，不得描述為推測的情緒狀態。
- **FR-EVT-005**：排隊中的前端事件只能在 API 接受後標記為已同步；離線或 API 失敗必須保留在前端重試機制中。
- **FR-EVT-006**：未來監督式排序可使用明確標籤，但已查看或忽略內容必須維持未標記，除非標籤政策另有定義。

## 8. 服務與 API 邊界

以下 P0 OpenAPI 已完成實作。P1 能力在 Feature SDD 核准前仍屬候選。

| 能力 | 端點 | 權責 |
|---|---|---|
| 建立可保存的匿名報告 | `POST /api/v2/reconstructions/complete` | Reconstruction Service |
| 將邀請碼交換為 Session | `POST /api/v2/auth/session` | Demo Identity Adapter |
| 認領報告 | `POST /api/v2/reports/{report_id}/claim` | Activation Service＋已驗證身份 |
| 確認報告持股 | `POST /api/v2/reports/{report_id}/confirmed-holdings` | Holding Service |
| 會員首頁 Aggregate | `GET /api/v2/me/dashboard` | Portfolio Radar Query Service |
| 提交卡片回饋 | `POST /api/v2/me/action-cards/{card_id}/feedback` | Feedback Service |
| 批次提交事件 | `POST /api/v2/events/batch` | Event Service |

P0 刻意透過 `GET /api/v2/me/dashboard` 聚合會員報告、Portfolio、優先卡片與每週回顧，以維持第一次會員頁 Render 的一致性並減少 Request Fan-out。關係維護與獨立卡片端點保留至 P1。

`/me` 代表伺服器從身份驗證結果取得身份。目前 `/users/{user_id}` 或 Request Body `user_id` 的模式不得成為正式會員授權邊界。

## 9. 資料模型需求

### 9.1 必要實體

| 實體 | 用途 |
|---|---|
| Reconstruction Report | 不可變更的驗證結果、匿名擁有者 Token、認領狀態與到期時間 |
| Report Claim | 具冪等性的報告至會員綁定與認領時間 |
| Portfolio Relationship | 已確認／僅觀察關係、來源、狀態與複核時間 |
| Market Moment | 確定性／模型證據、來源日期、特徵／模型版本與嚴重度 |
| Action Card | 市場時刻參照、會員情境、敘事來源與送達狀態 |
| Relationship Feedback | 最新回覆優先的明確回應與稽核歷史 |
| Reminder Preference | `routine`／`mute` 或後續頻率值；不得代表情緒 |
| Interaction Event | 具有事件發生時間與接收時間的冪等 Telemetry |

### 9.2 狀態轉移

```text
匿名報告：
created → completed_unclaimed → claimed
                         ↘ expired

持股候選：
candidate → consented → backend_revalidated → confirmed
                                      ↘ rejected

Portfolio 關係：
confirmed ↔ watch_only → removed
     ↘ stale_review_required
```

所有會改變身份歸屬或持股事實的狀態轉移都必須在伺服器端完成；預期會重試的操作必須冪等，且必須可稽核。

### 9.3 資料最小化

- 不可變更的報告可保存重播所需的已驗證重建輸出，但保存精確交易輸入前必須先定義保留政策。
- 已確認持股不要求價格、股數、券商或總資產。
- 公開分享圖卡預設不得包含股票 ID、價格、報告 ID 或報酬率。
- 模型訓練匯出資料必須以具範圍限制的假名識別碼取代直接身份，並記錄授權與標籤來源。
- 後續正式產品階段必須提供報告／關係刪除、匯出與撤回授權能力。

## 10. 非功能需求

- **NFR-001 — 安全性**：會員端點必須由伺服器取得身份，並防止跨會員存取報告或 Portfolio。
- **NFR-002 — 可靠性**：Bedrock／模型失敗不得阻擋確定性 Portfolio 與證據畫面。
- **NFR-003 — 可重現性**：歷史報告與模型產物必須包含資料範圍、特徵版本、模型版本與產生時間。
- **NFR-004 — 效能**：P0 會員首頁 Aggregate 目標為 p95 小於 1.5 秒，不含選配的非同步 AI 更新；可優先顯示快取或降級敘事。
- **NFR-005 — 無障礙**：卡片、分數與圖表必須具有文字替代內容，且操作可透過鍵盤完成。
- **NFR-006 — 可觀測性**：啟用、認領、卡片選擇、AI 降級與持久化失敗必須留下結構化 Log，但不得包含敏感輸入。
- **NFR-007 — 隱私**：Log 與 Analytics 不得記錄精確交易價格、身份 Token，或包含個資的完整生成 Prompt。
- **NFR-008 — 相容性**：留存實作必須維持在既有 React、FastAPI、PostgreSQL 與共用 Python Package 邊界內。

## 11. 驗收情境

### AS-01 — 匿名價值優先

**假設**陌生使用者尚未登入，**當**五筆交易全部通過驗證，**則**系統必須在要求註冊前顯示完整人格報告與分享圖卡。

### AS-02 — 認領不代表同意建立持股

**假設**使用者已認領報告，**當**尚未提交持股授權，**則**會員帳號只擁有報告，不得新增任何已確認持股。

### AS-03 — 明確銜接產生 Portfolio 價值

**假設**已認領報告包含三檔 `holding` 候選，**當**會員選擇其中兩檔並同意，**則** FastAPI 必須重新驗證報告，並建立恰好兩筆 `source=user_confirmed` 的已確認持股。

### AS-04 — 會員首頁只依已確認事實個人化

**假設**會員已有兩檔已確認持股，**當**開啟 `/app`，**則** Portfolio 模組必須只列出這兩筆關係，優先卡片也只能從符合條件的證據選取；未確認的測驗選股不得標示為持股。

### AS-05 — AI 失敗時柔性降級

**假設** Bedrock 逾時且模型產物不可用，**當**會員開啟 Portfolio Radar，**則**確定性 Portfolio／證據內容與固定模板 Action Card 仍必須顯示，且不得捏造數值。

### AS-06 — 回饋改變未來打擾策略，不改寫歷史

**假設**會員將 Action Card 設為 `mute`，**當**系統選擇下一張卡片，**則**打擾成本必須反映該偏好，但已認領的 2025 年報告與已確認關係歷史不得變更。

> **現況（部分達成）**：`mute`／`routine`／`review_evidence` 偏好已被持久化到
> `action_card_feedback`，且歷史不可變的部分已成立。但偏好**尚未改變下一張卡片的
> 排序**——Moment-Engine 的 ranking（打擾成本實際影響選卡）延後到未來 Feature 006。
> 目前應把 `mute` 描述為「已記錄、尚未作用」。

### AS-07 — 身份隔離

**假設**報告 A 屬於會員 A，**當**會員 B 要求存取或認領該報告，**則** API 必須拒絕操作，且不得洩漏會員 A 的身份或報告內容。

### AS-08 — 事件量測可安全重試

**假設**網路重試造成同一批事件提交兩次，**當**重新計算 Dashboard 指標，**則**每個事件只能計算一次。

## 12. 後續 SDD 交付切片

> **狀態更新（2026-07-15）**：P0 留存閉環（會員啟用、報告認領、report-scoped
> 持股授權、`/app` Portfolio Radar aggregate、卡片偏好與冪等事件）**已直接實作
> 出貨**——程式碼在 `apps/api/src/mindfolio_api/routers/retention.py` 與
> `apps/web/src/routes/{ActivateRoute,PortfolioRadarRoute}.tsx`。因此下表所列
> 004–007 的**功能已上線**，但對應的 per-feature SDD 資料夾
> (`docs/api/004..007`) **尚未建立**——這是一筆未結清的 paper-trail 追溯缺口，需
> 回填 spec/plan/tasks，而非重新開發。本節原先「必須先完成 004 SDD 才能動工」的
> 前置規範，對已出貨的 P0 範圍已不再適用（見 §16 決策紀錄與 §8「P0 OpenAPI 已完成
> 實作」）。

| Feature | 建議目錄 | 範圍 | 狀態 |
|---|---|---|---|
| 004 | `docs/api/004-member-activation` | 可保存報告、認領、Identity Adapter 與持股授權銜接 | 功能已上線；SDD 資料夾待回填 |
| 005 | `docs/api/005-portfolio-radar-home` | `/app` Aggregate、已認領指紋與已確認 Portfolio | 功能已上線；SDD 資料夾待回填 |
| 006 | `docs/api/006-market-moments-action-cards` | V1 Moment Engine 概念、排序、Bedrock 敘事與降級 | 部分上線（單張優先卡＋fallback 敘事已有；`mute` 影響排序的 Moment-Engine ranking 未做）；SDD 資料夾待回填 |
| 007 | `docs/api/007-events-preferences` | 冪等事件、關係回饋、提醒偏好與 Metrics | 功能已上線；SDD 資料夾待回填 |

每個 SDD Feature 必須包含：

1. 已釐清的 User Story 與失敗案例；
2. 凍結的 OpenAPI Request／Response Schema；
3. Database Migration 與資料擁有權規則；
4. 前端 Route／Component 與 Loading／Empty／Error 狀態；
5. Service／Repository／AI 邊界；
6. Unit、Integration、Contract 與 Acceptance Test；
7. 需求至測試的 Traceability；
8. 明確的 Rollback 與 Demo 降級行為。

原本的規範是「不得只依本整合文件直接開始後續實作，Feature 004 為第一個
Alignment Gate」。實務上 P0 已在此 gate 未逐項落檔的情況下出貨；因此該規範現在
改為**回填要求**：既有 P0 程式碼必須補上 004–007 的 spec/plan/tasks 以恢復
Traceability，而 P1／未完成項目（如 Moment-Engine ranking）仍應先過對應 Feature
SDD 再擴充。

## 13. 各交付階段範圍

### 黑客松 P0

- 結果頁會員價值預覽與啟用 CTA。
- 明確的 Demo Authentication 或 Identity Adapter。
- 認領一份重建報告。
- 後端重新驗證後，確認使用者選取的持股候選。
- 一個包含四個必要模組的 `/app` Portfolio Radar 頁面。
- 一張有證據依據且具確定性降級能力的 Action Card。
- 最小啟用、Portfolio 查看與卡片開啟事件。

### 黑客松後 P1

- 正式身份驗證整合。
- Portfolio 關係修正／移除與過期複核。
- 個股證據詳情頁。
- Event Outbox／重試與內部漏斗指標。
- 排程式每週回顧與提醒偏好。
- 與 2025 年重建隔離的即時／目前資料 Adapter。

### 本規格基準明確不包含

- 恢復或部署已封存的 V1 應用。
- 維護兩套 V1／V2 Database 或 API。
- 自由輸入式投資聊天機器人。
- 串接券商、強制要求股數／成本或上傳總資產。
- 股價預測、買賣建議、目標價或獲利保證。
- 第一個切片內的完整通知基礎設施。
- 在沒有有效標籤的情況下訓練持股預測或情緒模型。
- 在單頁留存循環尚未驗證前建立大型多頁 Dashboard。

## 14. 重用與遷移指引

V1 可作為下列需求與互動的參考：

- Market Moment 證據契約；
- 確定性卡片排序；
- Action Card Schema 與降級行為；
- 明確關係與提醒偏好回饋；
- 已確認 Portfolio 與事件管線語意。

重用任何程式碼前，SDD 規劃必須驗證其與目前 V2 Domain Model、`/api/v2` 契約、React State、PostgreSQL Schema 與隱私規則相容。V1 Route 名稱、Demo 身份、Database Schema 與生成產物不會自動成為權威來源。

## 15. 待 SDD 釐清事項

1. 黑客松 Demo 使用哪一種身份驗證機制？正式產品目標為何？
2. 完成的匿名報告可在多久內認領？
3. 為了重播報告，應保存哪些重建輸入？保留多久？
4. P0 應在 `/reconstructions/complete` 之前或執行期間建立報告？
5. 持股授權屬於啟用流程，還是 `/app` 的第一個操作？
6. 哪一份目前市場資料可在法律與技術上支援第一張 Portfolio Radar 卡？
7. Bedrock 敘事採同步、快取或非同步產生？
8. 如何定義持股關係已過期？何時需要重新確認？
9. 評審展示與正式 Analytics 分別需要哪些事件定義與漏斗指標？
10. 無目前資料時，P0 哪些區塊可以使用清楚標示的 Fixture？

## 16. 決策紀錄與開發歷程

| 日期 | 決策 | 影響 |
|---|---|---|
| 2026-07-14 | V2 維持為有效專案根目錄 | 所有新 Runtime Code 與 SDD Artifact 都放在 `V2/` |
| 2026-07-14 | Time Machine 負責獲客；Portfolio Radar 負責留存 | V1 與 V2 概念成為連續產品階段，不是競爭版本 |
| 2026-07-14 | V1 是封存參考，不是第二套 Runtime | 選定能力必須依 React + FastAPI + PostgreSQL 重新規格化 |
| 2026-07-14 | 本文件最初僅作需求文件 | 當時不將任何留存實作視為完成 |
| 2026-07-15 | P0 Time Machine → 啟用 → Portfolio Radar 已實作 | `/activate` 與 `/app` 成為有效會員旅程 |
| 2026-07-15 | 邀請碼交換為短效簽章 Session Token | 瀏覽器不保存可重複使用的邀請碼；正式產品仍以 CMoney SSO 為目標 |
| 2026-07-15 | 報告認領與持股授權分成兩次寫入 | 報告所有權不會默默建立持股關係 |
| 2026-07-15 | P0 使用一張明確標示 `as_of` 的歷史證據卡 | 不把 2025 年資料描述為即時市場情境 |
| 2026-07-15 | 前端 Analytics 使用冪等 Local Outbox | 失敗批次保留排隊並可重試，不重複計數 |
| 2026-07-15 | `/app` 完成四模組獨立導覽與介面狀態補強 | 補齊來源、未知欄位、低門檻 Follow-up、曝光事件與無障礙語意；不擴張至 P1 多頁 Dashboard |

## 17. 需求就緒定義

> **狀態更新（2026-07-15）**：下列前四項就緒條件在 P0 開發前均已滿足，P0 也已
> 據此出貨。唯一未落檔的是第五項——Feature 004 的獨立 Spec 尚未寫出（功能已上線，
> SDD 資料夾待回填，見 §12）。因此本節不再是「開工前的 gate」，而是記錄 P0 已就緒
> 並出貨、且標示出剩餘的 004–007 SDD 回填工作。

當初判定本整合需求可進入 Feature-Level SDD 的條件（現況）：

- Product Owner 確認 Time Machine → Portfolio Radar 銜接方式；（已確認）
- P0 與 P1 範圍獲得確認；（已確認）
- Identity 與 Report Claim 策略已選定；（已選定：邀請碼 Identity Adapter + 短效 Session Token + 報告認領）
- 目前資料來源與 Demo Fixture 政策已選定；（已選定）
- Feature 004 已有獨立 Spec，且不存在未解決的所有權或授權歧義。（**未落檔**：P0 直接出貨，004–007 SDD 資料夾待回填）

P0 獲客與留存皆已是實作真實來源；V1 維持唯讀參考。剩餘工作為回填 004–007 SDD
以恢復 Traceability，以及推進 P1／未完成項目（如 Moment-Engine ranking）。
