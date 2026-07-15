# Mindfolio Time Machine HTML 簡報

本目錄有三份簡報，皆離線可用、不依賴外部 CDN／字型／JS 套件：

- **[`pitch_v2.html`](pitch_v2.html) — 10 分鐘正式舞台版**：10 頁，依評分比重重排創新、技術、資料、AI、完成度；包含 3 分鐘 Live Demo 段落與真實 Bedrock 截圖。逐頁講稿見 [`pitch_v2.md`](pitch_v2.md)。
- **[`index.html`](index.html) — 20 頁正式繳交／詳細版**：完整技術、資料、模型指標、系統架構與交付狀態，供書面審查與 Q&A。
- **[`pitch.html`](pitch.html) — 舊 6 頁極短版**：保留作為時間被壓縮時的備援，不再是主要版本。

## 可直接繳交的 PDF

- [`mindfolio-time-machine-proposal-v2.pdf`](../../output/pdf/mindfolio-time-machine-proposal-v2.pdf)：20 頁正式提案文件。
- [`mindfolio-pitch-v2.pdf`](../../output/pdf/mindfolio-pitch-v2.pdf)：10 頁上台報告版本。

匯出 PDF：瀏覽器列印 → 橫向 → 邊界無 → 背景圖形開。

## 開啟方式（詳細版）

直接以瀏覽器開啟 [`index.html`](index.html)。簡報不依賴外部 CDN、字型或 JavaScript 套件，可離線展示。

## 頁數與報告方式

- 共 20 頁。
- 第 1～18 頁為約 10 分鐘主簡報。
- 第 19～20 頁為模型品質與交付狀態附錄，建議僅在 Q&A 使用。
- 每頁內建講者提示，按 `N` 顯示。

## 操作

| 操作 | 快捷鍵 |
|---|---|
| 下一頁 | `→`、`PageDown`、`Space` |
| 上一頁 | `←`、`PageUp` |
| 第一頁／最後一頁 | `Home`／`End` |
| 顯示講者提示 | `N` |
| 縮圖總覽 | `O` |
| 全螢幕 | `F` |

手機與平板可左右滑動切頁。

## 匯出 PDF

使用瀏覽器的「列印」功能，選擇：

- 方向：橫向
- 邊界：無
- 背景圖形：開啟
- 紙張：簡報已定義為 16:9（13.333 × 7.5 英吋）

列印版會自動隱藏控制列與講者提示，每頁輸出一張投影片。

## 內容依據

簡報以 V2 現行文件、程式與模型 Artifact 為準，核心來源為：

- `00_PROJECT_CHARTER.md`
- `03_DATA_AND_GUARDRAILS.md`
- `05_DEMO_RUNBOOK.md`
- `08_TECHNICAL_INNOVATION.md`
- `09_FRONTEND_BACKEND_ARCHITECTURE.md`
- `10_AI_TRAINING_PLAN.md`
- `12_V2_END_TO_END_SPEC.md`
- `13_ACQUISITION_RETENTION_INTEGRATION_SPEC.md`
- `14_AI_MINIMAL_INTEGRATION_SPEC.md`
- 專案根目錄 `CHANGELOG.md`

Bedrock Converse 已於線上 EC2 實測 live 且可用（短期 Bedrock API key 授權、evidence-grounded 敘事、「Bedrock 生成」badge）。Repo 預設 `bedrock_enabled=false`，部署環境明確開啟；任何外部失敗仍走 deterministic fallback。正式 IAM Role、HTTPS 與網域屬產品化強化，不再描述為本次 Demo 尚未打通。
