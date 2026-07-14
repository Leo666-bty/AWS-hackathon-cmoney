import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getHealth } from "../shared/api/client";

export function LandingRoute() {
  const health = useQuery({ queryKey: ["health"], queryFn: ({ signal }) => getHealth(signal) });

  return (
    <main className="page landing-page">
      <section className="hero-copy">
        <p className="eyebrow">CMONEY 2025 PORTFOLIO LAB</p>
        <h1>重建五檔記憶，<br /><em>看見你的投資人格。</em></h1>
        <p className="lead">
          不連券商、不上傳截圖。只要挑五檔熟悉的股票，提供大概月份與價格，
          後端引擎就會驗證行情、重建報酬並產生可分享的人格圖卡。
        </p>
        <div className="hero-actions">
          <Link className="button primary large" to="/builder">匿名開始重建 <span>→</span></Link>
          <small>約 2 分鐘・資料以 2025 年官方資料集為準</small>
        </div>
        <div className="hero-metrics">
          <article><b>300</b><span>檔股票可搜尋</span></article>
          <article><b>12</b><span>個月份回憶定位</span></article>
          <article><b>0</b><span>張個資截圖</span></article>
        </div>
      </section>

      <aside className="engine-preview">
        <header><span>RECONSTRUCTION ENGINE</span><i>{health.isSuccess ? "ONLINE" : "CHECKING"}</i></header>
        <div className="engine-flow"><b>選股</b><span>→</span><b>回憶</b><span>→</span><b>驗證</b><span>→</span><b>人格</b></div>
        <div className="terminal-lines">
          <p><i /> market catalog: 300 stocks</p>
          <p><i /> corporate action adjustment: enabled</p>
          <p><i /> financial truth: FastAPI verified</p>
          <p><i /> AI narrative: {health.data?.model_status ?? "fallback ready"}</p>
        </div>
        <div className="fingerprint-mini"><small>INVESTMENT FINGERPRINT</small><strong>LHDX</strong><span>低接・長抱・分散・精準</span></div>
      </aside>
    </main>
  );
}
