# Data

本目錄在本機保存 CMoney 主辦方提供的 workshop 簡報與 2025 CSV package。因公開再散布授權尚未確認，GitHub 不提交原始 PDF 與 CSV。

## 本機預期結構

```text
data/
├── AWS AI Hackathon - CMoney briefing 0702 .pdf
├── CMoney_Hackathon_Data_Workshop_20260702.pdf
├── Delivery_Hackathon_DataPackage_20260624/
│   ├── 00_Field_Dictionary_and_Usage_Notes.csv
│   ├── 01_Price_Valuation_2025.csv
│   └── ...
└── demo/
```

正式開發時由 API 的 CSV adapter 讀取這些檔案。公開 Demo 應只保留經驗證、無個資且足以重現畫面的最小資料子集。
