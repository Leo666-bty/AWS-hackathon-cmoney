# Growth & Sales Funnel

## 為什麼人格測驗適合做獲客入口

一般投資報告要求使用者先有問題、先輸入資料；人格測驗提供明確承諾、完成時間短、結果與自我認同有關，也自然適合分享。CMoney 的差異是結果不只靠文案，而是用真實 2025 報酬節點計算。

這不是 FAQ／ChatGPT 型入口：使用者不必先想問題或輸入 prompt，而是完成一個有明確終點的互動任務。AI 敘事提高理解與傳播，真正累積資料價值的是 Reconstruction Engine 與 confirmed holding consent。

## 10x 的兩個成長機制

### ① 匿名分享卡：Referral loop

人格卡提供可公開的身分標籤，但預設不包含股票、月份、價格、持股與報酬。每一次分享都能成為下一位陌生用戶的 Acquisition 入口：

```text
完成結果 → 分享圖卡 → 朋友點入 → 再完成一次 → 再分享
```

必須追蹤 `share_click`、`share_download`、referral source 與 referred reconstruction completion，不能只計算按鈕點擊就宣稱病毒成長。

### ② Progressive Profiling：Value-for-data ladder

每一層先交付可見價值，才請使用者提供下一層資料。任何一層拒絕都不得回收前一層已承諾的結果，也不得把候選／瀏覽誤記為真實持股。

## Pirate Funnel

| 階段 | 產品事件 | 核心指標 |
|---|---|---|
| Acquisition | 點擊朋友的人格卡／廣告 | Landing UV、來源別 CTR |
| Activation | 自選五檔並完成 Portfolio 重建 | 重建完成率、time-to-result |
| Referral | 分享匿名人格卡 | 分享率、分享帶入註冊數 |
| Revenue intent | 點擊解鎖完整報告 | CTA CTR、註冊完成率 |
| Retention | 開啟真實持股雷達、每週回顧 | D7/D30 回訪、雷達開啟率 |

## 三層產品交換

### Free：投資人格快測

- 不登入。
- 顯示人格、重建報酬、可信度、四項分數與分享卡。
- 目標：最大化完成與分享。

### Member：完整 2025 回放

- 建立 CMoney 帳號。
- 解鎖逐檔決策差異、同人格分布、如果改變一個決策的情境比較。
- 目標：把匿名流量轉成可聯繫會員。

### Portfolio：真實持股雷達

- 將重建時明確標記「仍持有」的股票帶入確認；股數與成本延後、可選填。
- 解鎖個人化法人／價格／社群背離與每週投資回顧。
- 目標：提高資料完整度與持續使用。

三層交換形成同一產品生命週期：Time Machine 負責 Free／Member acquisition，Portfolio Radar 負責 Portfolio retention。詳細 handoff 與 SDD requirements 見 `13_ACQUISITION_RETENTION_INTEGRATION_SPEC.md`。

## North Star 與漏斗資產

North Star 是 **Verified Holding Activation**：完成重建、明確同意，且後端成功
保存至少一檔仍持有關係的人數。

它比回答數、生成次數或人格測驗完成數更接近 CMoney 的商業價值，因為它同時代表：

- 使用者已收到足夠價值，願意完成資料交換；
- 股票關係來自明確同意，不是模型猜測；
- 後續 Portfolio Radar 有合法且相關的個人化基礎；
- CMoney 可以衡量從陌生流量到持股資料資產的完整轉換。

## 社群分享設計

分享卡文案示例：

> 我的 2025 投資人格是「趨勢配置師 THDX」。
>
> 我偏好價格確認後進場，並用多產業配置讓趨勢持續發展。你是哪一型？

公開卡片不顯示選股與報酬明細。報酬可讓使用者自行決定是否加到分享內容，預設關閉。

## 實驗矩陣

| 實驗 | A | B | 判斷指標 |
|---|---|---|---|
| Landing 主標 | 測投資人格 | 挑戰 2025 大盤 | 開始率 |
| 結果分享 | 只顯人格 | 人格＋分數區間 | 分享率 |
| 註冊交換 | 完整逐檔回放 | 同人格排行榜 | 註冊率 |
| Portfolio CTA | 開啟個人雷達 | 生成真實投資 DNA | 持股確認率 |

## Demo 目標，不冒充成效

黑客松 Demo 只能證明流程與事件可被量測，不能用單一測試 session 宣稱轉換提升。建議提案目標：

- Landing → 開始測驗 ≥ 35%
- 開始 → 完成 ≥ 65%
- 結果 → 分享 ≥ 12%
- 結果 → 註冊 CTA ≥ 15%
- 註冊 → 確認一檔真實持股 ≥ 30%
- 手動價格異常攔截後修正率 ≥ 60%

以上皆為上線後 A/B Test 的待驗證假設。
