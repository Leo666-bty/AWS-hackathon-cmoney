# Mindfolio AI Training

這個 app 是 **離線市場事件偵測管線**，不是使用者持股或焦慮預測服務。

它從 CMoney 官方的市場、法人與社群每日彙總資料建立特徵，訓練 `Market Moment Detector`，再輸出 API 可讀的 `MomentSignal`。線上 API 只讀取產物，不在使用者請求期間重新訓練。

## 三天 MVP 的訓練目標

回答一個有限且可驗證的問題：

> 在大量個股每日資料中，哪些時點出現值得優先呈現的異常、背離或熱度變化？

MVP 可採 `IsolationForest` 找異常，再用可解釋規則標記事件類型。它不回答：

- LEO 是否真的持有某檔股票
- LEO 是否焦慮
- 股票未來會漲或跌
- 應該買進或賣出

## 資料流

```text
CMoney CSV
  → API/Data Adapter 正規化欄位
  → build_features.py 建立 rolling features
  → train_moment_detector.py 訓練異常偵測器
  → score_moments.py 產生 MomentSignal JSONL
  → FastAPI 套用 Portfolio 與互動規則
  → Bedrock 將 evidence 轉成卡片文字
  → React 顯示卡片
```

## UI 實際使用方式

模型產物不直接決定文案或顏色。API 先把分數轉成穩定的產品規則：

| 模型輸出 | API／UI 用途 |
|---|---|
| `anomaly_score` | 決定卡片是否出現及排序，不直接顯示給使用者 |
| `moment_type` | 決定卡片標題模板、icon 與訊號標籤 |
| `severity` | 決定一般／注意／顯著三種視覺層級 |
| `evidence` | 產生可展開的法人、社群與價格證據 chips |
| `as_of` | 顯示資料日期，避免把歷史資料包裝成即時訊號 |

建議初始門檻：

```text
score < 0.65       不顯示主動卡片
0.65 <= score < .8 一般資訊卡
0.80 <= score < .9 注意卡
score >= .90       顯著事件；仍需結合持股關係與打擾成本決定是否置頂
```

這些門檻是 MVP 設定，不宣稱為已驗證的最佳值。

## 目錄

```text
contracts/                 MomentSignal JSON Schema
examples/                  2382 廣達的固定示例
src/mindfolio_training/    特徵、訓練與評分程式
artifacts/                 本機模型產物；除 .gitkeep 外不進 Git
```

## 正規化輸入欄位

訓練程式刻意不直接綁定主辦方原始 CSV 欄名。資料 Adapter 應先輸出：

```text
stock_id,date,close,institutional_net,bullish_count,bearish_count,post_count,reply_count
```

## 執行

```bash
cd apps/ai-training
python -m venv .venv
source .venv/bin/activate
pip install -e .

mindfolio-build-features normalized.csv artifacts/features.csv
mindfolio-train artifacts/features.csv artifacts/moment-detector.joblib
mindfolio-score artifacts/features.csv artifacts/moment-detector.joblib artifacts/moments.jsonl
```

若黑客松現場無法完成可靠訓練，API 必須降級使用 validated rules 與 `examples/2382-2025-12-31.json`，UI 閉環不可因此失效。
