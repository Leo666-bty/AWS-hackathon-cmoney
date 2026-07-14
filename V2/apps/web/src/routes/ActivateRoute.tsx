import { useMutation } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useReconstruction } from "../features/reconstruction/ReconstructionContext";
import {
  claimReport,
  confirmReportHoldings,
  createMemberSession,
  type SessionResponse,
} from "../shared/api/client";
import { getErrorMessage } from "../shared/api/errors";
import { trackEvent } from "../shared/analytics/events";
import { getAccessToken, saveMemberSession } from "../shared/auth/session";

export function ActivateRoute() {
  const navigate = useNavigate();
  const { result: response } = useReconstruction();
  const [inviteCode, setInviteCode] = useState("");
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [claimed, setClaimed] = useState(false);
  const candidates = response?.result.holding_candidates ?? [];
  const [selected, setSelected] = useState<string[]>(candidates);
  const report = response?.report;

  const activate = useMutation({
    mutationFn: async () => {
      if (!report) throw new Error("這份匿名報告目前無法保存，請稍後重新建立。");
      let accessToken = getAccessToken();
      let activeSession = session;
      if (!accessToken) {
        activeSession = await createMemberSession(inviteCode.trim());
        accessToken = activeSession.access_token;
        saveMemberSession(activeSession.access_token, activeSession.member_id);
        setSession(activeSession);
      }
      const claim = await claimReport(report.report_id, report.claim_token, accessToken);
      return { claim, activeSession };
    },
    onSuccess: () => {
      setClaimed(true);
      trackEvent("report_claimed", "activation", { action: "claim_success" });
    },
  });

  const confirm = useMutation({
    mutationFn: async () => {
      const accessToken = getAccessToken();
      if (!report || !accessToken) throw new Error("會員狀態已失效，請重新輸入邀請碼。");
      return confirmReportHoldings(report.report_id, selected, accessToken);
    },
    onSuccess: (holdings) => {
      trackEvent("holding_consent", "activation", {
        action: "confirmed",
        metadata: { holding_count: holdings.length },
      });
      void navigate("/app");
    },
  });

  const stockNames = useMemo(() => new Map(response?.result.trades.map((trade) => [trade.stock_id, trade.name]) ?? []), [response]);

  if (!response) return <Navigate to="/builder" replace />;

  return (
    <main className="page activation-page">
      <header className="activation-hero">
        <div><p className="eyebrow">MEMBER ACTIVATION</p><h1>保存這段投資旅程，<br /><em>開啟 Portfolio Radar。</em></h1><p>人格報告已經完整呈現。登入只用來跨階段保存報告，持股仍需下一步逐檔同意。</p></div>
        <aside><small>VALUE EXCHANGE</small><b>不是為了登入而登入</b><span>保存報告・確認庫存・每週證據回顧</span></aside>
      </header>

      <div className="activation-grid">
        <section className={`activation-step panel-card ${claimed ? "done" : "active"}`}>
          <header><span>01</span><div><p className="eyebrow">CLAIM REPORT</p><h2>認領匿名報告</h2></div><i>{claimed ? "✓" : ""}</i></header>
          <p>封測版採邀請碼身份隔離。正式商用可替換為 CMoney SSO，不改變報告與持股授權邏輯。</p>
          {!claimed && (
            <>
              {!getAccessToken() && <label className="invite-input">封測邀請碼<input type="password" autoComplete="one-time-code" value={inviteCode} onChange={(event) => setInviteCode(event.target.value)} placeholder="輸入團隊提供的邀請碼" /></label>}
              {getAccessToken() && <div className="session-ready">已偵測到這台裝置的會員工作階段</div>}
              <button className="button primary full" type="button" disabled={activate.isPending || (!getAccessToken() && inviteCode.trim().length < 6) || !report} onClick={() => activate.mutate()}>{activate.isPending ? "正在認領…" : "認領報告，下一步 →"}</button>
              {activate.isError && <div className="error-box">{getErrorMessage(activate.error)}</div>}
              {!report && <div className="error-box">報告保存服務暫時不可用；匿名結果仍可查看與分享。</div>}
            </>
          )}
          {claimed && <div className="success-box">報告已歸屬於 {session?.display_name ?? "目前會員"}，但尚未建立任何持股。</div>}
        </section>

        <section className={`activation-step panel-card ${claimed ? "active" : "locked"}`}>
          <header><span>02</span><div><p className="eyebrow">EXPLICIT HOLDING CONSENT</p><h2>選擇要加入庫存的股票</h2></div></header>
          <p>只有你勾選的「仍持有」候選會再次經後端驗證。股數、成本與券商保持未知。</p>
          <div className="consent-stock-list">
            {candidates.map((stockId) => (
              <label key={stockId}>
                <input type="checkbox" checked={selected.includes(stockId)} disabled={!claimed} onChange={() => setSelected((current) => current.includes(stockId) ? current.filter((id) => id !== stockId) : [...current, stockId])} />
                <span><b>{stockId} {stockNames.get(stockId)}</b><small>使用者確認持股・不保存價格</small></span>
              </label>
            ))}
          </div>
          <button className="button primary full" type="button" disabled={!claimed || confirm.isPending || selected.length === 0} onClick={() => confirm.mutate()}>{confirm.isPending ? "正在建立 Portfolio…" : `確認 ${selected.length} 檔並開啟 Radar →`}</button>
          {confirm.isError && <div className="error-box">{getErrorMessage(confirm.error)}</div>}
        </section>
      </div>
      <Link className="activation-back" to="/result">← 返回匿名結果；不認領也不會失去目前畫面</Link>
    </main>
  );
}
