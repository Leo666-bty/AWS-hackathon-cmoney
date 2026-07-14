import type { CardPreference, MemberDashboard } from "../../shared/api/client";

type DashboardReport = NonNullable<MemberDashboard["report"]>;
type DashboardCard = NonNullable<MemberDashboard["priority_card"]>;

const scoreRows = [
  { key: "outcome", label: "成果", max: 40 },
  { key: "entry", label: "進場", max: 25 },
  { key: "capture", label: "掌握", max: 20 },
  { key: "data", label: "資料", max: 15 },
] as const;

const feedbackLabels: Record<CardPreference, string> = {
  review_evidence: "幫我整理證據",
  routine: "只是例行查看",
  mute: "降低同類提醒",
};

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("zh-TW");
}

function answerFollowUp(question: string, card: DashboardCard): string {
  if (question.includes("法人")) {
    const evidence = card.evidence
      .filter((item) => item.label.includes("法人"))
      .map((item) => `${item.label} ${item.value}`)
      .join("、");
    return `${evidence || "法人資料不足"}。短期與較長區間方向不同時，只代表觀察尺度不同，不構成買賣訊號。`;
  }
  if (question.includes("社群") || question.includes("分母")) {
    return "社群比例是同學會對該股票的彙總討論訊號，不代表你的個人情緒，也不能單獨視為市場方向。";
  }
  if (question.includes("提醒") || question.includes("頻率")) {
    return "你的單鍵回饋只會調整同類內容的優先序與打擾成本，不會修改歷史報告或已確認持股。";
  }
  return `這張卡使用 ${card.as_of} 的封存資料，來源為 ${card.provenance}，不代表今天盤勢。`;
}

export function FingerprintPanel({ report }: { report: DashboardReport | null }) {
  return (
    <article id="fingerprint" className="fingerprint-panel panel-card" aria-labelledby="fingerprint-title">
      <header>
        <div><p className="eyebrow">PORTFOLIO FINGERPRINT</p><h2 id="fingerprint-title">你的 2025 投資人格</h2></div>
        <span>{report ? formatDate(report.created_at) : "尚未認領"}</span>
      </header>
      {report ? (
        <>
          <div className="radar-persona"><strong>{report.persona_code}</strong><div><b>{report.persona_name}</b><p>{report.persona_headline}</p></div></div>
          <div className="mini-scores" aria-label="投資人格四軸分數">
            {scoreRows.map(({ key, label, max }) => {
              const value = report.scores[key];
              const normalizedValue = Math.min(max, Math.max(0, value));
              return (
                <div key={key}>
                  <span>{label}</span>
                  <i role="progressbar" aria-label={`${label} ${value} 分`} aria-valuemin={0} aria-valuemax={max} aria-valuenow={normalizedValue}><b style={{ width: `${(normalizedValue / max) * 100}%` }} /></i>
                  <strong>{value}</strong>
                </div>
              );
            })}
          </div>
          <p className="data-note">重建信心 {report.confidence}／100・歷史報告不受後續市場資料改寫</p>
        </>
      ) : <div className="empty-module">尚未認領 Time Machine 報告。</div>}
    </article>
  );
}

export function ConfirmedPortfolioPanel({ portfolio }: { portfolio: MemberDashboard["portfolio"] }) {
  return (
    <article id="portfolio" className="portfolio-panel panel-card" aria-labelledby="portfolio-title">
      <header><div><p className="eyebrow">CONFIRMED PORTFOLIO</p><h2 id="portfolio-title">我的庫存</h2></div><span>{portfolio.length} 檔</span></header>
      <div className="portfolio-list">
        {portfolio.length ? portfolio.map((holding) => (
          <article className="holding-row" key={holding.stock_id}>
            <span className="holding-code">{holding.stock_id}</span>
            <div className="holding-identity"><b>{holding.name}</b><small>{holding.industry || "未分類"}</small></div>
            <div className="holding-state"><span className="verified-pill">本人確認</span><time dateTime={holding.confirmed_at}>複核 {formatDate(holding.confirmed_at)}</time></div>
            <div className="holding-unknowns" aria-label={`${holding.name} 尚未提供的資料`}><span>股數未知</span><span>成本未知</span></div>
          </article>
        )) : <div className="empty-module">沒有已確認持股；測驗選股不會自動出現在這裡。</div>}
      </div>
      <footer><span>來源只接受 user_confirmed</span><span>不需連接券商</span><span>敏感欄位保持選填</span></footer>
    </article>
  );
}

type PriorityCardProps = {
  card: DashboardCard | null;
  evidenceOpen: boolean;
  followUp: string | null;
  feedbackPending: boolean;
  feedbackError: string | null;
  onToggleEvidence: () => void;
  onFollowUp: (question: string) => void;
  onFeedback: (preference: CardPreference) => void;
};

export function PriorityActionCard({
  card,
  evidenceOpen,
  followUp,
  feedbackPending,
  feedbackError,
  onToggleEvidence,
  onFollowUp,
  onFeedback,
}: PriorityCardProps) {
  return (
    <section id="moment" className="priority-card panel-card" aria-labelledby="moment-title">
      <header>
        <div><p className="eyebrow">PRIORITY MARKET MOMENT</p><h2 id="moment-title">今日優先證據</h2></div>
        {card && <div className="source-badges"><span className="historical-badge">歷史資料・{card.as_of}</span><span className={`narrative-source ${card.narrative_source}`}>{card.narrative_source === "bedrock" ? "Bedrock 生成" : "規則備援"}</span></div>}
      </header>
      {card ? (
        <div className="moment-layout">
          <div className="moment-copy">
            <div className="stock-context"><span>{card.stock_id}</span><div><b>{card.stock_name}</b><small>因為這是你已確認的持股</small></div></div>
            <h3>{card.title}</h3>
            <p>{card.summary}</p>
            <button className="evidence-toggle" type="button" aria-expanded={evidenceOpen} aria-controls="moment-evidence" onClick={onToggleEvidence}>{evidenceOpen ? "收合證據" : "查看完整證據"} <span>→</span></button>
            {evidenceOpen && (
              <div id="moment-evidence" className="evidence-block">
                <div className="evidence-grid">{card.evidence.map((item) => <article className={item.tone} key={item.label}><small>{item.label}</small><strong>{item.value}</strong></article>)}</div>
                <p>資料來源：{card.provenance}・資料日期：{card.as_of}</p>
              </div>
            )}
            <div className="followup-block">
              <small>不用輸入 Prompt，直接選你想知道的</small>
              <div>{card.suggested_questions.map((question) => <button className={followUp === question ? "selected" : ""} type="button" key={question} aria-pressed={followUp === question} onClick={() => onFollowUp(question)}>{question}</button>)}</div>
              {followUp && <p role="status" aria-live="polite"><b>Mindfolio：</b>{answerFollowUp(followUp, card)}</p>}
            </div>
          </div>
          <aside className="moment-feedback" aria-labelledby="feedback-title">
            <p className="eyebrow">ONE-TAP FEEDBACK</p><h3 id="feedback-title">這類內容對你有什麼用途？</h3>
            {(Object.keys(feedbackLabels) as CardPreference[]).map((preference) => <button className={card.current_preference === preference ? "selected" : ""} type="button" key={preference} disabled={feedbackPending} aria-pressed={card.current_preference === preference} onClick={() => onFeedback(preference)}><i />{feedbackLabels[preference]}{card.current_preference === preference && <span>已儲存</span>}</button>)}
            {feedbackError && <div className="feedback-error" role="alert">{feedbackError}</div>}
            <p>這是內容偏好，不是心理診斷或焦慮分數。</p>
          </aside>
        </div>
      ) : <div className="empty-module large">確認至少一檔仍持有股票後，系統才會選出個人化市場卡。</div>}
    </section>
  );
}

export function WeeklyReviewPanel({ review }: { review: MemberDashboard["weekly_review"] }) {
  return (
    <section id="weekly" className="weekly-review panel-card" aria-labelledby="weekly-title">
      <div><div className="weekly-heading"><p className="eyebrow">WEEKLY REVIEW</p><span>{review.source === "snapshot" ? "目前快照預覽" : "Demo Fixture"}</span></div><h2 id="weekly-title">{review.title}</h2><p>{review.summary}</p><small>摘要資料截至 {review.data_as_of}；正式排程與即時資料屬 P1。</small></div>
      <aside><small>NEXT REVIEW</small><strong>{new Date(review.next_review_at).toLocaleDateString("zh-TW", { month: "short", day: "numeric" })}</strong><span>沒有高影響證據時不打擾</span></aside>
    </section>
  );
}
