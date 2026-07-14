import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { defaultTrade, useReconstruction } from "../features/reconstruction/ReconstructionContext";
import {
  completeReconstruction,
  getMonthEnvelope,
  validateTrade,
  type StockSummary,
  type TradeConfig,
} from "../shared/api/client";
import { getErrorMessage } from "../shared/api/errors";

const monthLabel = (month: string) => `${Number(month)} 月`;
const formatPrice = (value: number) => value.toLocaleString("zh-TW", { maximumFractionDigits: 2 });

function TradeEditor({ stock, index }: { stock: StockSummary; index: number }) {
  const navigate = useNavigate();
  const { selected, trades, dispatch } = useReconstruction();
  const [draft, setDraft] = useState<TradeConfig>(() => trades[stock.id] ?? defaultTrade(stock));
  const [message, setMessage] = useState<string | null>(null);
  const envelope = useQuery({
    queryKey: ["envelope", stock.id, draft.buy_month],
    queryFn: ({ signal }) => getMonthEnvelope(stock.id, draft.buy_month, signal),
  });
  const validate = useMutation({ mutationFn: validateTrade });
  const complete = useMutation({ mutationFn: completeReconstruction });

  const sellMonths = useMemo(
    () => stock.available_months.filter((month) => Number(month) > Number(draft.buy_month)),
    [draft.buy_month, stock.available_months],
  );

  const normalizedDraft: TradeConfig = {
    ...draft,
    buy_mode: envelope.data && !envelope.data.allowed_price_modes.includes("band") ? "exact" : draft.buy_mode,
    sell_month: draft.relation === "sold" && !sellMonths.includes(draft.sell_month)
      ? (sellMonths.at(-1) ?? "12")
      : draft.sell_month,
  };

  const submit = async () => {
    setMessage(null);
    if (normalizedDraft.buy_mode === "exact" && (!normalizedDraft.buy_exact || normalizedDraft.buy_exact <= 0)) {
      setMessage("請輸入有效的實際買進價格。");
      return;
    }
    if (normalizedDraft.relation === "sold" && sellMonths.length === 0) {
      setMessage("這檔股票在買進月份後沒有足夠行情可重建賣出結果。");
      return;
    }
    if (normalizedDraft.relation === "sold" && normalizedDraft.sell_mode === "exact" && (!normalizedDraft.sell_exact || normalizedDraft.sell_exact <= 0)) {
      setMessage("請輸入有效的實際賣出價格。");
      return;
    }
    try {
      const validation = await validate.mutateAsync(normalizedDraft);
      if (!validation.valid) {
        setMessage(validation.message);
        return;
      }
      dispatch({ type: "set-trade", trade: normalizedDraft });
      if (index < 4) {
        void navigate(`/reconstruct/${index + 1}`);
        return;
      }
      const completedTrades = selected.map((item) => item.id === stock.id ? normalizedDraft : trades[item.id]);
      if (completedTrades.some((trade) => !trade)) {
        setMessage("尚有股票未完成設定，請回到前一步補齊。");
        return;
      }
      const validTrades = completedTrades.filter((trade): trade is TradeConfig => Boolean(trade));
      const result = await complete.mutateAsync(validTrades);
      dispatch({ type: "set-result", result });
      void navigate("/result");
    } catch (error) {
      setMessage(getErrorMessage(error));
    }
  };

  const isBusy = envelope.isPending || validate.isPending || complete.isPending;

  return (
    <main className="page stage-page narrow">
      <header className="stage-head compact">
        <div><p className="eyebrow">STEP 2 / 3 · STOCK {index + 1} / 5</p><h1>{stock.id} {stock.name}</h1><p>只需提供大概月份；若記得價格，可切換精確模式提升信心分數。</p></div>
      </header>
      <div className="config-progress"><span style={{ width: `${((index + 1) / 5) * 100}%` }} /></div>
      <section className="trade-editor panel-card">
        <div className="trade-stock"><span>{stock.id}</span><div><h2>{stock.name}</h2><p>{stock.industry || "未分類"}・2025 年資料</p></div></div>

        <fieldset>
          <legend>1. 你大約何時買進？</legend>
          <div className="month-grid">
            {stock.available_months.map((month) => <button className={draft.buy_month === month ? "active" : ""} key={month} type="button" onClick={() => setDraft({ ...draft, buy_month: month })}>{monthLabel(month)}</button>)}
          </div>
        </fieldset>

        <fieldset>
          <legend>2. 價格記憶精度</legend>
          <div className="segmented">
            <button className={normalizedDraft.buy_mode === "band" ? "active" : ""} type="button" disabled={!envelope.data?.allowed_price_modes.includes("band")} onClick={() => setDraft({ ...draft, buy_mode: "band", buy_exact: null })}>用區間回憶</button>
            <button className={normalizedDraft.buy_mode === "exact" ? "active" : ""} type="button" onClick={() => setDraft({ ...draft, buy_mode: "exact" })}>我記得實際價格</button>
          </div>
          {envelope.data && (
            <div className={`envelope-note ${envelope.data.corporate_action ? "warning" : ""}`}>
              <b>當月行情 {formatPrice(envelope.data.raw_low)}–{formatPrice(envelope.data.raw_high)}</b>
              <span>{envelope.data.corporate_action ? "此月有公司行動，必須輸入實際價格" : "後端將用還原因子驗證與計算"}</span>
            </div>
          )}
          {normalizedDraft.buy_mode === "band" ? (
            <div className="band-options">
              {(["low", "mid", "high"] as const).map((band) => <button className={draft.buy_band === band ? "active" : ""} type="button" key={band} onClick={() => setDraft({ ...draft, buy_band: band })}>{band === "low" ? "偏低" : band === "mid" ? "中間" : "偏高"}</button>)}
            </div>
          ) : (
            <label className="price-input">實際買進價格<input inputMode="decimal" type="number" min="0" step="0.01" value={draft.buy_exact ?? ""} onChange={(event) => setDraft({ ...draft, buy_exact: event.target.value ? Number(event.target.value) : null })} /></label>
          )}
        </fieldset>

        <fieldset>
          <legend>3. 2025 年底仍持有嗎？</legend>
          <div className="segmented">
            <button className={draft.relation === "holding" ? "active" : ""} type="button" onClick={() => setDraft({ ...draft, relation: "holding" })}>仍持有</button>
            <button className={draft.relation === "sold" ? "active" : ""} type="button" onClick={() => setDraft({ ...draft, relation: "sold" })}>已賣出</button>
          </div>
          {draft.relation === "sold" && (
            <div className="sell-fields">
              <label>賣出月份<select value={normalizedDraft.sell_month} onChange={(event) => setDraft({ ...draft, sell_month: event.target.value })}>{sellMonths.map((month) => <option key={month} value={month}>{monthLabel(month)}</option>)}</select></label>
              <div className="segmented compact-options"><button className={draft.sell_mode === "estimate" ? "active" : ""} type="button" onClick={() => setDraft({ ...draft, sell_mode: "estimate", sell_exact: null })}>用月末價估算</button><button className={draft.sell_mode === "exact" ? "active" : ""} type="button" onClick={() => setDraft({ ...draft, sell_mode: "exact" })}>輸入實際價</button></div>
              {draft.sell_mode === "exact" && <label className="price-input">實際賣出價格<input inputMode="decimal" type="number" min="0" step="0.01" value={draft.sell_exact ?? ""} onChange={(event) => setDraft({ ...draft, sell_exact: event.target.value ? Number(event.target.value) : null })} /></label>}
            </div>
          )}
        </fieldset>

        {(message || envelope.isError) && <div className="error-box">{message ?? getErrorMessage(envelope.error)}</div>}
        <footer className="form-actions">
          <button className="button secondary" type="button" onClick={() => index === 0 ? navigate("/builder") : navigate(`/reconstruct/${index - 1}`)}>← 上一步</button>
          <button className="button primary" type="button" disabled={isBusy || envelope.isError} onClick={submit}>{complete.isPending ? "後端重建中…" : index === 4 ? "產生投資人格 →" : "儲存並下一檔 →"}</button>
        </footer>
      </section>
    </main>
  );
}

export function ReconstructionRoute() {
  const { selected } = useReconstruction();
  const { index = "0" } = useParams();
  const currentIndex = Number(index);
  if (selected.length !== 5) return <Navigate to="/builder" replace />;
  if (!Number.isInteger(currentIndex) || currentIndex < 0 || currentIndex > 4) return <Navigate to="/reconstruct/0" replace />;
  return <TradeEditor key={selected[currentIndex].id} stock={selected[currentIndex]} index={currentIndex} />;
}
