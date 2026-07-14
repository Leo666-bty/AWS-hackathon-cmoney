import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Navigate } from "react-router-dom";
import {
  ConfirmedPortfolioPanel,
  FingerprintPanel,
  PriorityActionCard,
  WeeklyReviewPanel,
} from "../features/portfolio-radar/PortfolioRadarModules";
import { getMemberDashboard, saveCardFeedback, type CardPreference } from "../shared/api/client";
import { getErrorMessage } from "../shared/api/errors";
import { trackEvent } from "../shared/analytics/events";
import { clearMemberSession, getAccessToken } from "../shared/auth/session";

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

      <WeeklyReviewPanel review={data.weekly_review} />
    </main>
  );
}
