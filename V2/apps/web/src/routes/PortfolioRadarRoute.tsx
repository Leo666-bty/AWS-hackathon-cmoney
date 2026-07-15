import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Navigate } from "react-router-dom";
import {
  ConfirmedPortfolioPanel,
  FingerprintPanel,
  PriorityActionCard,
  WeeklyReviewPanel,
} from "../features/portfolio-radar/PortfolioRadarModules";
import {
  askInvestmentQuestion,
  generateInvestmentAIReport,
  getMemberDashboard,
  saveCardFeedback,
  type CardPreference,
  type InvestmentQuestionId,
} from "../shared/api/client";
import { getErrorMessage } from "../shared/api/errors";
import { trackEvent } from "../shared/analytics/events";
import { clearMemberSession, getAccessToken } from "../shared/auth/session";

function formatEvidenceRef(ref: string): string {
  const trade = /^trade:(\d+)$/.exec(ref);
  if (trade) return `第 ${Number(trade[1]) + 1} 筆交易`;
  const market = /^market:([^:]+):(\d{4}-\d{2})$/.exec(ref);
  if (market) return `${market[1]}・${market[2]} 市場情境`;
  return ref;
}

function formatEvidenceRefs(refs: string[]): string {
  return refs.map(formatEvidenceRef).join("・");
}

export function PortfolioRadarRoute() {
  const queryClient = useQueryClient();
  const token = getAccessToken();
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [followUp, setFollowUp] = useState<string | null>(null);
  const trackedDashboard = useRef(false);
  const trackedCardId = useRef<string | null>(null);

  const dashboard = useQuery({
    queryKey: ["member-dashboard"],
    queryFn: ({ signal }) => getMemberDashboard(token ?? "", signal),
    enabled: Boolean(token),
    retry: false,
  });

  const feedback = useMutation({
    mutationFn: ({ cardId, preference }: { cardId: string; preference: CardPreference }) => saveCardFeedback(cardId, preference, token ?? ""),
    onSuccess: (_, variables) => {
      trackEvent("card_feedback", "portfolio_radar", { action: variables.preference });
      void queryClient.invalidateQueries({ queryKey: ["member-dashboard"] });
    },
  });

  const deepDive = useMutation({
    mutationFn: (reportId: string) => generateInvestmentAIReport(reportId, token ?? ""),
    onMutate: () => trackEvent("ai_report_open", "portfolio_radar"),
    onSuccess: (report) => trackEvent("ai_report_generated", "portfolio_radar", { action: report.source }),
  });

  const question = useMutation({
    mutationFn: ({ reportId, questionId }: { reportId: string; questionId: InvestmentQuestionId }) => askInvestmentQuestion(reportId, questionId, token ?? ""),
    onMutate: ({ questionId }) => trackEvent("ai_question_chip_click", "portfolio_radar", { action: questionId }),
    onSuccess: (answer) => trackEvent(answer.source === "fallback" ? "ai_answer_fallback" : "ai_answer_rendered", "portfolio_radar", { action: answer.question_id }),
  });

  useEffect(() => {
    if (dashboard.isSuccess && !trackedDashboard.current) {
      trackedDashboard.current = true;
      trackEvent("portfolio_view", "portfolio_radar");
    }
  }, [dashboard.isSuccess]);

  useEffect(() => {
    const card = dashboard.data?.priority_card;
    if (card && trackedCardId.current !== card.card_id) {
      trackedCardId.current = card.card_id;
      trackEvent("action_card_impression", "portfolio_radar", { stock_id: card.stock_id });
    }
  }, [dashboard.data?.priority_card]);

  if (!token) return <Navigate to="/activate" replace />;
  if (dashboard.error && "status" in dashboard.error && dashboard.error.status === 401) {
    clearMemberSession();
    return <Navigate to="/activate" replace />;
  }

  if (dashboard.isPending) {
    return <main className="page radar-page"><div className="radar-loading panel-card" role="status"><i /><h1>正在整理你的 Portfolio Radar</h1><p>先載入已確認持股，再選出今天最值得看的證據。</p></div></main>;
  }
  if (dashboard.isError) {
    return <main className="page radar-page"><div className="error-state panel-card" role="alert"><p className="eyebrow">PORTFOLIO RADAR UNAVAILABLE</p><h1>目前無法載入個人雷達</h1><p>{getErrorMessage(dashboard.error)}</p><button className="button primary" type="button" onClick={() => dashboard.refetch()}>重新載入</button></div></main>;
  }

  const data = dashboard.data;
  const card = data.priority_card;
  const portfolioCompletion = Math.min(100, 40 + data.portfolio.length * 12);

  const toggleEvidence = () => {
    setEvidenceOpen((current) => {
      if (!current && card) trackEvent("card_evidence_open", "portfolio_radar", { stock_id: card.stock_id });
      return !current;
    });
  };

  const selectFollowUp = (question: string) => {
    setFollowUp(question);
    if (card) trackEvent("ai_followup_open", "portfolio_radar", { stock_id: card.stock_id, action: question });
  };

  const saveFeedback = (preference: CardPreference) => {
    if (!card) return;
    feedback.reset();
    feedback.mutate({ cardId: card.card_id, preference });
  };

  return (
    <main className="page radar-page">
      <header className="radar-hero" id="overview">
        <div><p className="eyebrow">PORTFOLIO RADAR</p><h1>{data.display_name}，你的投資脈絡<br /><em>已從一次報告開始累積。</em></h1><p>只針對已確認關係提供個人化內容；市場與社群證據不會被描述成你的情緒。</p></div>
        <div className="freshness-card"><small>PORTFOLIO STATUS</small><strong>{data.portfolio.length}</strong><span>檔已確認持股</span><i role="progressbar" aria-label={`Portfolio 完整度 ${portfolioCompletion}%`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={portfolioCompletion}><b style={{ width: `${portfolioCompletion}%` }} /></i><p>股數與成本可保持未知，不影響基本陪伴</p></div>
      </header>

      <nav className="radar-section-nav" aria-label="Portfolio Radar 區塊導覽">
        <a href="#fingerprint">投資人格</a><a href="#portfolio">我的庫存</a><a href="#moment">優先證據</a><a href="#weekly">每週回顧</a>
        <button type="button" disabled={dashboard.isFetching} onClick={() => dashboard.refetch()}>{dashboard.isFetching ? "更新中…" : "更新雷達"}</button>
      </nav>

      <section className="radar-grid">
        <FingerprintPanel report={data.report} />
        <ConfirmedPortfolioPanel portfolio={data.portfolio} />
      </section>

      <PriorityActionCard
        card={card}
        evidenceOpen={evidenceOpen}
        followUp={followUp}
        feedbackPending={feedback.isPending}
        feedbackError={feedback.isError ? getErrorMessage(feedback.error) : null}
        onToggleEvidence={toggleEvidence}
        onFollowUp={selectFollowUp}
        onFeedback={saveFeedback}
      />

      <section id="deep-dive" className="ai-deep-dive panel-card" aria-labelledby="deep-dive-title">
        <header>
          <div><p className="eyebrow">AI DEEP DIVE</p><h2 id="deep-dive-title">從交易記憶回看市場情境</h2></div>
          {deepDive.data && <span>{deepDive.data.source === "bedrock" ? "Bedrock 生成" : "安全備援"}</span>}
        </header>
        {!data.report ? <div className="empty-module">先認領 Time Machine 報告，才能建立個人化解讀。</div> : !deepDive.data ? (
          <div className="deep-dive-gate">
            <p>系統會把五筆重建結果與買進月份的市場 regime、法人及全站社群證據串在一起。沒有自由聊天，也不會產生買賣建議。</p>
            <button className="button primary" type="button" disabled={deepDive.isPending} onClick={() => deepDive.mutate(data.report!.report_id)}>{deepDive.isPending ? "正在整理歷史證據…" : "產生 AI 深度解讀"}</button>
            {deepDive.isError && <p className="feedback-error" role="alert">{getErrorMessage(deepDive.error)}</p>}
          </div>
        ) : (
          <div className="deep-dive-content">
            <h3>{deepDive.data.title}</h3>
            <p className="deep-dive-summary">{deepDive.data.executive_summary}</p>
            <div className="deep-dive-columns">
              <div><small>代表性成果</small>{deepDive.data.strengths.map((section) => <article key={section.title}><b>{section.title}</b><p>{section.body}</p><code aria-label="證據來源">{formatEvidenceRefs(section.evidence_refs)}</code></article>)}</div>
              <div><small>值得回看</small>{deepDive.data.watchouts.map((section) => <article key={section.title}><b>{section.title}</b><p>{section.body}</p><code aria-label="證據來源">{formatEvidenceRefs(section.evidence_refs)}</code></article>)}</div>
              <div><small>買進月份情境</small>{deepDive.data.market_moments.map((section) => <article key={section.title}><b>{section.title}</b><p>{section.body}</p><code aria-label="證據來源">{formatEvidenceRefs(section.evidence_refs)}</code></article>)}</div>
            </div>
            <div className="deep-dive-questions">
              <small>不用輸入 Prompt，直接選一個問題</small>
              <div>{deepDive.data.suggested_questions.map((item) => <button type="button" key={item.id} disabled={question.isPending} onClick={() => question.mutate({ reportId: data.report!.report_id, questionId: item.id })}>{item.label}</button>)}</div>
              {question.data && <article role="status"><b>Mindfolio：</b><p>{question.data.answer}</p><small>{question.data.limitations}</small><code aria-label="證據來源">{formatEvidenceRefs(question.data.evidence_refs)}</code></article>}
              {question.isError && <p className="feedback-error" role="alert">{getErrorMessage(question.error)}</p>}
            </div>
          </div>
        )}
      </section>

      <WeeklyReviewPanel review={data.weekly_review} />
    </main>
  );
}
