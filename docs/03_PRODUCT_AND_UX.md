# Product & UX

## 產品原則

> Zero Prompt、Zero Upload、One Tap first。

使用者照常使用籌碼 K 線。AI 出現在原本的自選股與個股研究流程中，不要求先聊天、上傳截圖或填完整 Portfolio。

## MVP 資訊架構

| 介面 | 使用者任務 | 系統取得的資料 |
|---|---|---|
| 自選股 | 選擇要研究的股票 | `watchlist_view`、`stock_open` |
| 個股頁 | 看即時、盤後、社群、新聞 | `stock_tab_view`、`card_evidence_open`、`news_open` |
| AI 情境卡 | 理解背離並回覆關係 | `card_impression`、`relationship_feedback` |
| 情境式追問 | 點選已建議的問題，不必打字 | `ai_followup_open` |
| Concern Signal | 回覆有點擔心、例行查看或不用提醒 | `concern_feedback` |
| 我的庫存 | 查看已確認關係與今日優先事件 | `portfolio_view`、`holding_removed` |
| 營運 Dashboard | 驗證互動漏斗與事件同步 | 即時事件表與四個 MVP 指標 |

## 完整使用流程

```text
LEO 從自選股開啟 2382 廣達
→ 查看盤後法人、社群與新聞
→ AI 主動呈現「法人 × 社群背離」
→ LEO 查看證據
→ 一鍵選擇：是我的持股／只是觀察／不相關
→ AI 改用正確的個人情境語氣
→ LEO 可點選建議追問，無須自由輸入
→ LEO 回覆目前是否需要提醒
→ 我的庫存與 Dashboard 即時更新
```

## 為什麼不以聊天為主

ChatGPT 式入口要求使用者自己發現問題、組織 Prompt、等待答案。Mindfolio 把互動改成：系統先用資料判斷值得注意的時刻，再提供三個一鍵行動與三個建議追問。聊天能力仍存在，但被壓縮成 context-aware follow-up，而不是空白輸入框。

## Concern Signal，不是假焦慮分數

市場與社群資料只能說明股票情境，不能診斷 LEO。MVP 只在洞察後問：

- 有點擔心：後續優先整理證據，不放大情緒。
- 例行查看：不提高通知頻率。
- 不用提醒：降低同類卡片優先度。

只有使用者明確點擊才成為個人資料。

## 新聞範圍

新聞是個股研究體驗的一部分，也可提供 `news_open` context。官方 package 沒有新聞，因此 MVP Reference 使用明確標示的 Demo Feed；Live MVP 若無授權來源，不得偽裝成官方新聞。

## 推播定位

推播是後續通路，不是三天核心工程。MVP 先證明站內卡片具備：正確時機、簡單按鈕、可回饋、可降低打擾。正式推播只針對已確認持股與高影響事件，同日最多一則。

## UX 禁止事項

- 不以聊天輸入框作為首頁。
- 不使用截圖上傳。
- 不把候選關係寫成真實持股。
- 不顯示虛假的持股準確率或焦慮分數。
- 不把全站社群資料寫成 LEO 的情緒。
- 不在首次回饋收成本、股數、券商與總資產。
