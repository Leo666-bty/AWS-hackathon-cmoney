# Data & AI

## 官方資料能做什麼

| 資料 | 用途 |
|---|---|
| 價格與估值 | 收盤、報酬、估值情境 |
| 法人動向 | 單日與 20 日籌碼趨勢 |
| 高低點／年線距離 | 價格位置情境 |
| 股利／產業 | 基本屬性與分類 |
| 社群每日彙總 | 發回文量、明確多空方向與熱度 |

資料基準日固定為 **2025-12-31**。

## 官方資料不能做什麼

- 不含真實持股 Ground Truth。
- 不含 member ID 或個人瀏覽事件。
- 不含貼文原文，不能做留言 NLP。
- 不能用社群總體資料判定 LEO 焦慮。
- 不能從資料推測精確成本、股數與配置。

## Demo 使用者資料來源

LEO 的 `holding/watch_only/irrelevant` 只來自前台一鍵回饋。若正式整合 CMoney 既有產品行為，可作為 Moment Engine 的排序特徵，但不能假裝它存在於本次 CSV package。

MVP 會即時收集 `stock_tab_view`、`news_open`、`card_evidence_open`、`relationship_feedback`、`concern_feedback` 與 `ai_followup_open`。這些資料可驗證產品漏斗，也可在未來累積足夠明確標籤後訓練排序模型。

## AI 分工

### Deterministic Python

- 20 日法人買賣超
- 7 日明確多空貼文比例
- 變化率、排名、異常值
- `relevance × impact × novelty − interruption_cost`
- 輸出可驗證 evidence JSON

### Amazon Bedrock

- 將 evidence 轉為簡潔自然語言
- 依 schema 產生卡片標題、摘要與三個行動
- 依已確認關係切換「持股／觀察」語氣
- 遵守非投資建議與禁止推測規則
- 回答使用者點選的 contextual follow-up；不建立空白 ChatGPT 對話入口

### Concern Signal

`worried/routine/mute` 是使用者主動回覆，不是模型診斷。MVP 不輸出 Anxiety Score；未來若有足夠同意且可撤回的個人行為資料，也只能做「提醒需求」預測，不能包裝成心理健康判定。

### News

官方 package 不含新聞。Prototype 的兩則內容必須標示 `MVP Demo Feed` 與 `is_demo=true`，只用於驗證 `news_open` 與 Context 組合；正式產品改接有授權的 CMoney 新聞資料。

### 離線 Market Moment Detector

官方資料沒有個人持股或焦慮標籤，因此不訓練持股預測與焦慮診斷模型。三天 MVP 的模型範圍收斂為：使用市場、法人與社群每日資料訓練無監督異常偵測器，找出值得優先呈現的背離、熱度與異常時點。

訓練與評分程式位於 `apps/ai-training`。輸出是包含 `moment_type`、`anomaly_score`、`severity` 與 `evidence` 的 `MomentSignal`，再交由 API 結合 LEO 已確認的股票關係與打擾成本排序。

模型不直接產生 UI 文案，也不把 anomaly score 當作使用者焦慮分數。Bedrock 只負責將已驗證 evidence 轉成結構化卡片。

| Training output | UI 效果 |
|---|---|
| anomaly score | 決定卡片是否出現及先後順序；不直接顯示數字 |
| moment type | 決定背離、熱度或法人異常的標籤與模板 |
| severity | 決定一般、注意、顯著三層視覺強度 |
| evidence | 顯示可展開的法人、社群、價格證據 |
| as-of date | 明確標示資料日期 |

三天後可再使用明確的 relationship feedback、concern feedback 與卡片互動，訓練「哪張卡值得先出現」的 ranking model，而不是猜精確庫存。

## 廣達 Demo Evidence

```json
{
  "stock_id": "2382",
  "as_of": "2025-12-31",
  "close": 272,
  "institutional_net_20d": -60265,
  "community_bullish_ratio_7d": 0.939,
  "community_ratio_scope": "explicit_bullish_or_bearish_posts_only",
  "signal": "community_institution_divergence"
}
```

## 卡片輸出 Schema

```json
{
  "card_type": "signal_divergence",
  "title": "市場很樂觀，法人卻仍在調節",
  "evidence": [
    "近20日法人賣超60265張",
    "明確多空貼文中93.9%偏多"
  ],
  "actions": [
    "是我的持股",
    "只是觀察",
    "不相關"
  ]
}
```

## Guardrails

- 所有數字由程式算好後再交給 LLM。
- 回覆不得出現買進、賣出、目標價或保證獲利。
- 每張卡保留 source date 與 evidence。
- LLM 輸出不符合 JSON schema 時使用固定模板降級。
