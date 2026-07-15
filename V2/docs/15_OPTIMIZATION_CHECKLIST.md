# Post-P0 Optimization Backlog

| 欄位 | 內容 |
|---|---|
| 文件狀態 | Backlog / Not in current development scope |
| 更新日期 | 2026-07-15 |
| 前置條件 | `14_AI_MINIMAL_INTEGRATION_SPEC.md` P0 驗收完成 |
| 原則 | 不阻擋黑客松 Demo；只有 P0 穩定後才依證據排入 |

## 1. 文件目的

本文件保留 P0 之後的優化候選，不代表本次三天 MVP 的承諾範圍，也不得為了完成
清單而擴大目前架構。P0 source of truth 仍是 `14_AI_MINIMAL_INTEGRATION_SPEC.md`。

## 2. P1：Demo 後優先處理

### 2.1 真實 AWS Runtime 驗證

- 以 EC2 IAM Role 驗證 Bedrock `converse`。
- 驗證 timeout、invalid schema、guardrail hit 與 fallback telemetry。
- 記錄 AI report latency、fallback rate 與單次生成成本。

### 2.2 正式身份與資料生命週期

- 以 CMoney SSO 取代 invite-code adapter。
- 加入登出、token rotation、report deletion 與 holding consent withdrawal。
- 定義資料保存期限與會員刪除流程。

### 2.3 Migration 與部署自動化

- 導入正式 migration runner，不再依賴 empty-volume init scripts。
- CI 驗證 migration forward path、API image build、React build 與 smoke tests。
- 建立 EC2 HTTPS、網域、備份與 rollback runbook。

### 2.4 AI 品質校正

- 人工抽樣檢查 regime label 與 anomaly evidence precision。
- 以 domain review 校正 centroid naming；避免同義或不具區辨力的 labels。
- 建立 prompt regression fixtures 與 evidence-ref hallucination tests。
- 將模型 metrics、artifact checksum 與 UI 使用率放入 release report。

### 2.5 E2E 測試

- Playwright 覆蓋 Time Machine → Result → Activate → Portfolio Radar → AI Deep Dive。
- 覆蓋 report ownership、過期 claim、Bedrock failure 與 cache hit。
- 測試 mobile breakpoint、keyboard navigation 與 loading/error states。

## 3. P2：取得真實互動資料後評估

### 3.1 排序模型

- 使用 `card_impression`、`evidence_open`、`mute`、`ai_question_chip_click` 訓練內容排序。
- 未回答事件不得直接標成 negative label。
- 指標使用 Precision@K、NDCG、coverage 與 interruption penalty。

### 3.2 Artifact 發布流程

- S3 versioned artifact registry。
- 排程重訓、model approval gate 與 rollback。
- 新舊 artifact shadow comparison；runtime 仍維持 fail-soft。

### 3.3 Live CMoney Context

- 將即時／盤後資料放在獨立 Live Context adapter。
- 不得回寫或改變 immutable 2025 reconstruction report。
- 建立資料新鮮度、來源時間與 stale fallback。

### 3.4 產品實驗

- AI Deep Dive 解鎖率。
- 三個問題 chips 的 CTR 與 completion rate。
- Deep Dive 使用者的 7-day return rate。
- Portfolio confirmation 與 retention uplift 的 A/B test。

## 4. 維持不做

- 自由聊天作為主要入口。
- 截圖上傳或強制券商串接。
- Multi-Agent、RAG、Vector DB，除非有明確資料與檢索需求。
- 使用市場社群資料診斷個人情緒。
- 股價、報酬、買賣點或真實持股預測。

## 5. 排程 Gate

任何 backlog 項目進入開發前，至少回答：

1. 它改善哪一個已量測 KPI？
2. P0 現有模組是否能直接擴充？
3. 是否增加新的服務、資料表或部署 failure domain？
4. 三天 MVP 是否真的需要？若否，留在本文件。
