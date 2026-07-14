import { useQuery } from "@tanstack/react-query";
import { getHealth } from "../shared/api/client";

const foundations = [
  ["React + TypeScript", "前端互動與 API 呈現"],
  ["FastAPI + Python", "可信驗證、計算與 AI inference"],
  ["AI Training", "Offline models 與版本化 artifacts"],
];

export function FoundationRoute() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => getHealth(signal),
  });

  const apiLabel = health.isPending
    ? "正在檢查 FastAPI…"
    : health.isSuccess
      ? `${health.data.service} · ${health.data.status}`
      : "FastAPI 尚未啟動";

  return (
    <main className="foundation-shell">
      <header className="foundation-header">
        <div className="brand-mark">M</div>
        <div>
          <strong>Mindfolio Time Machine</strong>
          <span>V2 PROJECT FOUNDATION</span>
        </div>
      </header>

      <section className="foundation-hero">
        <p className="eyebrow">PROJECT INITIALIZED</p>
        <h1>前後端與 AI Training<br /><em>已建立共同基礎。</em></h1>
        <p>
          目前是專案骨架，不是完成版產品。下一步將依文件逐一實作股票搜尋、
          Portfolio Reconstruction 與模型 inference。
        </p>
        <div className={`api-status ${health.isSuccess ? "online" : "offline"}`}>
          <i />
          <span>{apiLabel}</span>
          {health.isError && <button onClick={() => health.refetch()}>重新檢查</button>}
        </div>
      </section>

      <section className="foundation-grid" aria-label="專案架構">
        {foundations.map(([title, copy], index) => (
          <article key={title}>
            <small>0{index + 1}</small>
            <h2>{title}</h2>
            <p>{copy}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
