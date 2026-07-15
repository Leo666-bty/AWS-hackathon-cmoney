import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useReconstruction } from "../features/reconstruction/ReconstructionContext";
import lacCard from "../assets/personality-cards/lac-contrarian-scout.webp";
import ladCard from "../assets/personality-cards/lad-low-entry-rotator.webp";
import lhcCard from "../assets/personality-cards/lhc-deep-concentrator.webp";
import lhdCard from "../assets/personality-cards/lhd-low-entry-collector.webp";
import tacCard from "../assets/personality-cards/tac-trend-striker.webp";
import tadCard from "../assets/personality-cards/tad-momentum-rotator.webp";
import thcCard from "../assets/personality-cards/thc-theme-navigator.webp";
import thdCard from "../assets/personality-cards/thd-trend-allocator.webp";

const personaImages: Record<string, string> = {
  LHD: lhdCard,
  LHC: lhcCard,
  LAD: ladCard,
  LAC: lacCard,
  THD: thdCard,
  THC: thcCard,
  TAD: tadCard,
  TAC: tacCard,
};

const formatReturn = (value: number) => `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`;
const formatPrice = (value: number) => value.toLocaleString("zh-TW", { maximumFractionDigits: 2 });

export function ResultRoute() {
  const { result: response } = useReconstruction();
  const [copied, setCopied] = useState(false);

  if (!response) return <Navigate to="/builder" replace />;
  const { result, narrative } = response;
  const personaPrefix = result.persona_code.slice(0, 3);
  const cardImage = personaImages[personaPrefix] ?? personaImages.LHD;
  const shareText = `我的 2025 投資人格是「${result.persona_name} ${result.persona_code}」！${result.persona_headline} #Mindfolio #投資時光機`;
  const copyShare = async () => {
    try {
      await navigator.clipboard.writeText(shareText);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };

  const scoreRows = [
    ["成果", result.scores.outcome, 40],
    ["進場", result.scores.entry, 25],
    ["掌握", result.scores.capture, 20],
    ["資料", result.scores.data, 15],
  ] as const;

  return (
    <main className="page result-page">
      <section className="result-hero">
        <div><p className="eyebrow">YOUR INVESTMENT FINGERPRINT</p><div className="persona-title"><strong>{result.persona_code}</strong><span>{result.persona_name}</span></div><h1>{narrative.headline}</h1><p>{narrative.summary}</p><div className="result-actions"><button className="button primary" type="button" onClick={copyShare}>{copied ? "已複製匿名文案" : "分享人格結果"}</button><a className="button secondary" href={cardImage} download={`mindfolio-${personaPrefix.toLowerCase()}.png`}>下載圖卡</a></div></div>
        <aside className="confidence-card"><small>資料重建可信度</small><strong>{result.confidence}</strong><span>/ 100</span><p>由後端依價格驗證、月份完整度與輸入精度計算</p></aside>
      </section>

      <section className="result-summary-grid">
        <article><p className="eyebrow">2025 RECONSTRUCTED RETURN</p><h2>五檔等權重推估報酬</h2><strong className={result.average_return >= 0 ? "positive" : "negative"}>{formatReturn(result.average_return)}</strong><p>未計交易稅、手續費與滑價，不等於券商損益。</p></article>
        <article><p className="eyebrow">CONFIRMED CANDIDATES</p><h2>仍持有候選</h2><strong>{result.holding_candidates.length} / 5</strong><p>{result.holding_candidates.join("、") || "本次沒有標記仍持有的股票"}</p></article>
      </section>

      <section className="result-layout">
        <article className="share-card panel-card">
          <img src={cardImage} alt={`${result.persona_name}人格分享圖卡`} />
          <div><p className="eyebrow">ANONYMOUS SHARE CARD</p><h2>分享人格，不公開持股</h2><p>圖卡不包含股票、價格、月份或報酬明細。</p></div>
        </article>
        <article className="narrative-card panel-card"><p className="eyebrow">AI NARRATIVE · {narrative.source === "bedrock" ? "BEDROCK 生成" : "安全備援文案"}</p><h2>{narrative.insight}</h2><p>AI 只敘述後端驗證完成的 DTO；模型失敗時自動改用固定模板，不重新計算金融數字。</p></article>
      </section>

      <section className="panel-card report-panel">
        <header className="panel-heading"><div><p className="eyebrow">PORTFOLIO TIMELINE</p><h2>五檔重建結果</h2></div><span>月份級估算</span></header>
        <div className="trade-table">
          <div className="trade-row trade-head"><span>股票</span><span>買進</span><span>退出／年底</span><span>關係</span><span>推估報酬</span><span>信心</span></div>
          {result.trades.map((trade) => <div className="trade-row" key={trade.stock_id}><span><b>{trade.stock_id}</b> {trade.name}</span><span>{Number(trade.buy_month)} 月 · {formatPrice(trade.buy_raw)}</span><span>{Number(trade.exit_month)} 月 · {formatPrice(trade.exit_raw)}</span><span>{trade.relation === "holding" ? "仍持有" : "已賣出"}</span><span className={trade.return_pct >= 0 ? "positive" : "negative"}>{formatReturn(trade.return_pct)}</span><span>{trade.confidence}</span></div>)}
        </div>
      </section>

      <section className="panel-card report-panel">
        <header className="panel-heading"><div><p className="eyebrow">DECISION BREAKDOWN</p><h2>2025 情境決策力</h2></div><span>不等於真實投資能力</span></header>
        <div className="score-grid">
          {scoreRows.map(([label, value, max]) => <article key={label}><div><b>{label}</b><span>{value} / {max}</span></div><i><span style={{ width: `${(value / max) * 100}%` }} /></i></article>)}
        </div>
        <div className="vector-box"><span>Portfolio Fingerprint</span><code>[{result.fingerprint.map((value) => value.toFixed(3)).join(", ")}]</code></div>
      </section>

      <section className="consent-panel panel-card">
        <div><p className="eyebrow">FROM ACQUISITION TO RETENTION</p><h2>保存報告，開啟 Portfolio Radar</h2><p>先認領這份匿名報告，再逐檔確認「仍持有」候選。認領後可解鎖買進月份的市場情境與三個證據型追問；認領不等於同意建立持股。</p><div className="value-list"><span>跨階段保存人格報告</span><span>只追蹤本人確認持股</span><span>解鎖市場情境 AI Deep Dive</span></div></div>
        {response.report ? <Link className="button primary" to="/activate">保存報告並開啟 Radar →</Link> : <button className="button primary" type="button" disabled>報告保存服務暫時不可用</button>}
      </section>

      <p className="disclaimer">此結果依使用者回憶的月份與價格重建，屬估算情境；人格不是心理診斷，分數不代表未來績效，內容不構成投資建議。</p>
    </main>
  );
}
