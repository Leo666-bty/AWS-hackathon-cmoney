# Project Charter

## 專案名稱

**Mindfolio Time Machine — Portfolio Reconstruction Engine**

> 讓陌生用戶用五檔熟悉股票重建 2025 投資軌跡，先得到人格與投報率，再主動確認仍持有的股票。

## 問題

CMoney 擁有大量市場資料，但陌生用戶不會為了未知價值先登入、連券商或填完整庫存。固定題目的娛樂測驗容易分享，卻無法累積真實持股，也不足以展現技術能力。

FAQ／ChatGPT 型應用還有另一個根本限制：使用者必須先想到問題、輸入 prompt，產品才開始提供價值。這不適合作為大規模陌生開發入口，也容易停留在「LLM 外面包一層 UI」，無法累積 CMoney 獨有的資料資產。

## 為什麼這不是 FAQ 型 AI

- **Zero Prompt**：使用者是來玩一趟 2025 投資時光機，不必先理解 AI、組織問題或上傳券商資料。
- **AI 不是金融真相來源**：報酬、價格合理性、公司行動、可信度與人格向量都由可重算的 Python service 產生。
- **人格是傳播層**：Bedrock／LLM 將 verified DTO 寫成易懂、可分享的敘事，失敗時使用固定模板。
- **Reconstruction Engine 是護城河**：把「大概三月買、差不多這個價」轉成行情驗證、公司行動還原、附可信度的結構化重建事件；持股關係仍須由使用者明確確認。
- **Portfolio Radar 是長期價值**：V2 Time Machine 取得陌生用戶與第一筆資料；註冊後由 Portfolio Radar 延續 V1 的 Market Moment／Action Card 能力，形成回訪理由。

## 解法

把「人格測驗」升級為持股重建流程：

1. 熱門推薦降低開始成本。
2. 300 檔搜尋讓內容貼近個人經驗。
3. 月份與價格區間降低回憶門檻。
4. 時間價格驗證攔截明顯異常輸入。
5. 還原因子讓公司行動前後價格可比較。
6. 人格與匿名分享負責獲客，仍持有確認負責 Portfolio 建檔。

## 10x 陌生用戶機制

成長不是來自「AI 回答更多問題」，而是兩個可量測機制疊加：

1. **匿名分享卡**：結果具身分認同與比較性，又不公開股票、價格與金額；分享帶入下一個陌生 session，形成 referral loop。
2. **Progressive Profiling**：Free 先提供人格、報酬與分享卡；Member 用完整回放換註冊；Portfolio 用持股雷達與每週回顧換取明確確認的持股資料。

```text
分享卡帶入陌生人
→ Time Machine 完成與再次分享
→ 註冊認領完整報告
→ 確認持股並開啟 Portfolio Radar
→ 持續回訪與補充資料
```

## North Star

**Verified Holding Activation**：完成重建並主動標記至少一檔「2025-12-31 仍持有」的匿名或已註冊使用者數。

## Demo 必須證明

- 熱門推薦是由資料排序，不是寫死行銷名單。
- 任意五檔都能完成月份級買賣重建。
- 亂填價格會被月份行情範圍拒絕。
- 公司行動不會直接造成錯誤投報率。
- Result 同時顯示報酬、可信度與技術 pipeline。
- 只有使用者明確選擇「仍持有」才形成 confirmed holding。

## 技術決策

- 正式產品採前後端分離，Frontend 使用 React + TypeScript。
- React Frontend 不持有完整市場資料，也不負責正式計算。
- Backend 使用 FastAPI + Python，統一承擔驗證、報酬、Fingerprint、人格與 AI orchestration。
- deterministic finance calculation 與 AI 共用 Python environment，但維持不同 service boundary。
- Offline AI training 與 FastAPI 共用 feature definitions 與 model contract，不在 request path 訓練。
- React × FastAPI vertical slice 已完成：8 支 API、300 檔 catalog、逐筆驗證、五檔 complete、AI fallback 與 confirmed holdings。V2 Python suite 58 tests 與 React build 通過；`V2/demo/` 保留為靜態 UX reference。

## 非目標

- 不驗證券商真實成交紀錄。
- 不從價格合理推論交易一定存在。
- 不把估算報酬當作真實總資產績效。
- 不做買賣建議、未來預測或心理診斷。
