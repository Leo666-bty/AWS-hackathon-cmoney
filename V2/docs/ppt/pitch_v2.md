# Mindfolio Pitch V2｜10 分鐘舞台講稿

## 時間配置

| 區段 | 時間 | 投影片 |
|---|---:|---|
| 問題與創新 | 2:05 | 1–3 |
| Live Demo | 3:00 | 4 |
| 技術、資料與 AI | 3:20 | 5–8 |
| 商業價值與收尾 | 1:20 | 9–10 |
| 緩衝 | 0:15 | 換頁／切換瀏覽器 |

## 上台原則

1. 先講使用者行為障礙，再講 AI；不要以技術棧開場。
2. 不說「AI 猜真實持股」；只有本人明確確認後才是 confirmed holding。
3. 不把人格、報酬或市場分類說成 Bedrock 算的；金融數字全部來自 deterministic engine。
4. 不把社群彙總說成個人焦慮；它只代表股票層市場情境。
5. 不宣稱 ML 預測漲跌；KMeans 與 IsolationForest 只描述歷史情境與異常。
6. Bedrock 可明確說「已在線上 EC2 實測 live」，並補充任何失敗都有 deterministic fallback。

## 必講金句

### 開場

> CMoney 已經非常懂股票，但要做到真正個人化，還缺一件事：使用者手上到底抱著什麼。問題是，真實持股是最難取得的資料。我們的答案很反直覺：先別問他。

### 創新

> 我們突破的不是 ChatGPT 的回答能力，而是資料取得方式：讓使用者先匿名得到價值，再逐層交換資料，最後只用一次明確同意，形成可用的持股關係。

### 技術

> LLM 可以寫得很好，但不能負責金融真相。Mindfolio 的報酬、人格與可信度由可重算的 Reconstruction Engine 產生，同輸入必定同輸出。

### 資料與 AI

> 官方 CSV 同時支撐產品計算與 AI 訓練：價格資料負責驗證投資記憶；價量、法人與社群彙總形成 3,584 個 stock-month 情境。離線 ML 找情境，Bedrock 把已驗證證據寫成人話。

### 收尾

> 三分鐘的時光機，換來第一筆本人確認的持股關係。我們不是打造另一個 ChatGPT；而是讓不想聊天的投資人，也願意被 AI 理解。

## Live Demo 操作

1. `/`：選擇五檔股票。
2. `/builder`：輸入月份與價格區間。
3. 故意填入明顯錯價，展示 FastAPI Price Envelope 驗證。
4. 修正後完成 `/reconstruction`，進入 `/result`。
5. 展示人格、重建報酬與資料可信度。
6. `/activate` 輸入 `123456` 或 `000000`。
7. 獨立勾選仍持有股票，進入 `/app`。
8. 點開 AI Deep Dive，指出「Bedrock 生成」badge 與 evidence refs。

> EC2 目前為 HTTP，台上不要操作依賴 `navigator.clipboard` 的分享按鈕。

## 評審追問速答

### 你們真的有訓練 AI 嗎？

有。離線訓練 KMeans Market Regime 與 IsolationForest anomaly detector，使用 3,584 個 stock-month、8 個月度特徵。模型產物預先評分並以 SHA-256 checksum 發布；線上 API O(1) 查表，不載入 sklearn。

### Bedrock 做了什麼？

Bedrock Converse 使用 `openai.gpt-oss-120b-1:0`，只接收 verified DTO，輸出結構化繁體中文 Deep Dive。Pydantic schema、evidence refs 與投資建議 guardrail 限制輸出；已在線上 EC2 實測 live，失敗時自動 fallback。

### 為什麼不用聊天框？

既有 WebUI ChatGPT 使用率低，證明自由 Prompt 並非低門檻互動。V2 改用流程式選擇、固定問題 chips 與證據卡，讓使用者用點選完成互動。

### 你們怎麼知道是真實持股？

測驗股票、歷史重建事件與目前持股是三種不同語意。只有報告認領後，由使用者在獨立 Consent Gate 明確選擇「仍持有」，後端再次驗證 report scope，才寫入 confirmed holding。
