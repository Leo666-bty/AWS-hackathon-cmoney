# Mindfolio Time Machine V2

> 從 300 檔股票重建五檔持股，讓陌生用戶在得到投資人格與投報率的同時，主動留下可驗證的持股資料。

V2 不再是固定五檔歷史選擇題。使用者可以從 CMoney 熱門推薦開始，也能搜尋主辦方 300 檔股票資料庫；每檔只需提供買進月份、價格區間或實際價格，以及仍持有或賣出月份。`Portfolio Reconstruction Engine` 會驗證價格合理性、處理公司行動、重建投報率並生成投資指紋。

## 目標技術架構

正式 V2 採前後端分離。前端使用 **React + TypeScript**；後端統一使用 **FastAPI + Python**，讓行情計算、資料驗證、Portfolio Fingerprint、AI training inference 與 AI narrative 共用同一個 Python runtime。

```text
React + TypeScript Frontend
  → FastAPI REST API
      → Stock / Price Repository
      → Reconstruction & Scoring Services
      → AI Narrative Service
      → Trained Model Inference
      → PostgreSQL / CMoney Data
```

目前 `demo/` 是靜態 UX reference，內嵌資料與前端計算只用來示範流程，不代表正式安全邊界。正式版的價格驗證、報酬、可信度、人格向量與 AI context 必須全部由 FastAPI 重算。

## 核心閉環

```text
熱門推薦／300 檔搜尋
→ 自選五檔熟悉股票
→ 買進月份＋區間或實際價格
→ 仍持有／賣出月份
→ 價格異常驗證＋公司行動校正
→ 投報率＋投資人格＋資料可信度
→ 匿名分享
→ 註冊保存
→ 只將「仍持有」寫入已確認 Portfolio
```

## 快速入口

- [可操作 Demo](demo/index.html)
- [文件中心](docs/README.md)
- [資料生成與來源](data/README.md)
- [資料庫快照產生器](tools/build_market_catalog.py)
- [前後端分離架構](docs/09_FRONTEND_BACKEND_ARCHITECTURE.md)
- [AI Training 計畫](docs/10_AI_TRAINING_PLAN.md)

## Demo 能力

- 依 CMoney 同學會瀏覽人數顯示熱門股票。
- 搜尋 300 檔股票代號、名稱與產業。
- 每檔可選 2025 任一有行情的買進月份。
- 價格可選月內偏低／中間／偏高區，或輸入實際成交價。
- 手動價格超出該月高低範圍時不允許送出。
- 已賣出可選賣出月份與估算／實際價格；仍持有則計算至 12/31。
- 以還原因子校正拆股、除權息後的可比較報酬。
- 產出 Portfolio Fingerprint、人格、情境決策力與資料可信度。

## 重要聲明

月份與價格來自使用者回憶，結果是重建估算，不是券商交易證明。價格合理性檢查只能攔截明顯亂填，不能證明交易真的發生。人格不是心理診斷，分數不代表未來績效，內容不構成投資建議。
