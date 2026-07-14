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

### 不做模型訓練

官方資料沒有個人持股標籤，三天內訓練「持股預測模型」沒有可靠 Ground Truth。硬做模型只會製造虛假準確率。MVP 的 AI 價值在資料融合、事件排序與結構化生成。

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
