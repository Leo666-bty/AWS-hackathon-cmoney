# Reconstruction, Personality & Scoring

## Portfolio Fingerprint

引擎將五檔重建事件轉成五維向量：

```text
[entry_position, holding_duration, sector_diversity, input_precision, normalized_return]
```

- `entry_position`：成交價在買進月份高低範圍中的平均位置。
- `holding_duration`：買進至賣出／年底的平均月份長度。
- `sector_diversity`：以五檔產業占比計算的 `1 - HHI`。
- `input_precision`：實際價格輸入占比。
- `normalized_return`：只用於視覺化的區間正規化報酬。

## 人格四軸

| 軸 | 低側 | 高側 | 來源 |
|---|---|---|---|
| L / T | Low-entry 低接 | Trend-confirmed 順勢 | 月內成交位置 |
| H / A | Hold 長抱 | Active 主動 | 仍持有比例與持有月份 |
| D / C | Diversified 分散 | Concentrated 集中 | 產業 HHI |
| X / E | Exact 精準 | Estimated 估算 | 實際價格輸入比例 |

人格名稱由前三軸決定，第四軸描述資料精度。這是可解釋的產品分類，不是心理學量表。

## 八個主要人格

| 前綴 | 名稱 |
|---|---|
| LHD | 低接收藏家 |
| LHC | 深潛集中派 |
| LAD | 低點輪動者 |
| LAC | 逆勢狙擊手 |
| THD | 趨勢配置師 |
| THC | 主題領航員 |
| TAD | 動能輪動者 |
| TAC | 趨勢突擊手 |

## 報酬重建

每筆使用者原始成交價先乘上該月 adjustment factor，再計算：

```text
return = adjusted_exit_price / adjusted_entry_price - 1
portfolio_return = 五檔 return 的等權重平均
```

選擇區間時使用區間代表值；持有者以 12 月最後交易日還原收盤價為 exit；已賣出但未填實際賣價者以賣出月最後交易日估算。

## 資料可信度

- 實際買價通過月行情驗證：基礎 100。
- 價格區間估算：基礎 78。
- 賣出價使用月末估算：減 8。
- 買進或出場月偵測到公司行動：減 15。
- 單檔最低不低於 45；結果顯示五檔平均。

可信度衡量「重建資料精度」，不是交易真實性。

## 2025 情境決策力

| 維度 | 權重 | 說明 |
|---|---:|---|
| 報酬結果 | 40 | 五檔等權重重建報酬區間化 |
| 進場位置 | 25 | 成交價在當月區間的位置 |
| 報酬捕捉 | 20 | 離場價相對後續月末價格 |
| 資料完整 | 15 | 重建可信度換算 |

總分與分項只適用這次事後回看情境，不得包裝為真實投資能力。
