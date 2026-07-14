import { useQuery } from "@tanstack/react-query";
import { useDeferredValue, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useReconstruction } from "../features/reconstruction/ReconstructionContext";
import { getPopularStocks, searchStocks, type StockSummary } from "../shared/api/client";
import { getErrorMessage } from "../shared/api/errors";

function StockRow({ stock, selected, disabled, onToggle }: {
  stock: StockSummary;
  selected: boolean;
  disabled: boolean;
  onToggle: () => void;
}) {
  return (
    <button className={`stock-row ${selected ? "selected" : ""}`} type="button" onClick={onToggle} disabled={disabled && !selected}>
      <span className="stock-code">{stock.id}</span>
      <span><b>{stock.name}</b><small>{stock.industry || "未分類"}・{stock.available_months.length} 個月份</small></span>
      <span className="stock-views">{stock.views.toLocaleString()} 人看過</span>
      <i>{selected ? "✓" : "+"}</i>
    </button>
  );
}

export function BuilderRoute() {
  const navigate = useNavigate();
  const { selected, dispatch } = useReconstruction();
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query.trim());
  const popular = useQuery({ queryKey: ["stocks", "popular"], queryFn: ({ signal }) => getPopularStocks(12, signal) });
  const search = useQuery({
    queryKey: ["stocks", "search", deferredQuery],
    queryFn: ({ signal }) => searchStocks(deferredQuery, signal),
    enabled: deferredQuery.length > 0,
  });
  const activeQuery = deferredQuery ? search : popular;
  const results = activeQuery.data ?? [];

  const quickPick = () => {
    if (!popular.data) return;
    const selectedIds = new Set(selected.map((stock) => stock.id));
    popular.data.slice(0, 5).forEach((stock) => {
      if (!selectedIds.has(stock.id) && selectedIds.size < 5) {
        dispatch({ type: "toggle-stock", stock });
        selectedIds.add(stock.id);
      }
    });
  };

  return (
    <main className="page stage-page">
      <header className="stage-head">
        <div><p className="eyebrow">STEP 1 / 3</p><h1>選出五檔你熟悉的股票</h1><p>熱門排序來自 CMoney 同學會瀏覽數，也可搜尋 300 檔 2025 股票資料。</p></div>
      </header>
      <div className="builder-grid">
        <section className="stock-browser panel-card">
          <label className="search-box"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="輸入股票代號、名稱或產業" /><b>300 檔</b></label>
          <div className="section-title"><h2>{deferredQuery ? "搜尋結果" : "2025 熱門推薦"}</h2><button type="button" onClick={quickPick}>帶入熱門五檔</button></div>
          {activeQuery.isError && <div className="error-box">{getErrorMessage(activeQuery.error)} <button onClick={() => activeQuery.refetch()}>重試</button></div>}
          <div className="stock-results" aria-live="polite">
            {activeQuery.isPending && <div className="skeleton-list">正在讀取股票資料…</div>}
            {!activeQuery.isPending && results.length === 0 && <div className="empty-state">找不到符合條件的股票。</div>}
            {results.map((stock) => (
              <StockRow
                key={stock.id}
                stock={stock}
                selected={selected.some((item) => item.id === stock.id)}
                disabled={selected.length >= 5}
                onToggle={() => dispatch({ type: "toggle-stock", stock })}
              />
            ))}
          </div>
        </section>

        <aside className="selected-panel panel-card">
          <header><div><small>YOUR FIVE</small><h2>我的五檔股票</h2></div><strong>{selected.length} / 5</strong></header>
          <div className="selected-list">
            {Array.from({ length: 5 }, (_, index) => {
              const stock = selected[index];
              return stock ? (
                <button key={stock.id} type="button" onClick={() => dispatch({ type: "toggle-stock", stock })}>
                  <span>{index + 1}</span><b>{stock.id} {stock.name}</b><i>×</i>
                </button>
              ) : <div className="empty-slot" key={index}><span>{index + 1}</span>等待選擇</div>;
            })}
          </div>
          <button className="button primary full" type="button" disabled={selected.length !== 5} onClick={() => navigate("/reconstruct/0")}>開始重建買賣記憶 →</button>
          <p>選股只是匿名測驗素材；只有最後標記「仍持有」並同意保存的股票才會寫入庫存。</p>
        </aside>
      </div>
    </main>
  );
}
