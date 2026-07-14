# Source Layout

正式開工時依下列最小模組建立 Python package：

```text
main.py
routes/
services/
repositories/
models/
prompts/
```

Day 1 先以固定的 LEO demo data 跑通 contract；接著才把 CSV adapter 接入，不先建立大型資料管線。
