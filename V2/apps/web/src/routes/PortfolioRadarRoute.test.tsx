import "@testing-library/jest-dom/vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MemberDashboard } from "../shared/api/client";
import { saveMemberSession } from "../shared/auth/session";
import { PortfolioRadarRoute } from "./PortfolioRadarRoute";

const { askInvestmentQuestion, generateInvestmentAIReport, getMemberDashboard, saveCardFeedback, trackEvent } = vi.hoisted(() => ({
  askInvestmentQuestion: vi.fn(),
  generateInvestmentAIReport: vi.fn(),
  getMemberDashboard: vi.fn<() => Promise<MemberDashboard>>(),
  saveCardFeedback: vi.fn(),
  trackEvent: vi.fn(),
}));

vi.mock("../shared/api/client", () => ({ askInvestmentQuestion, generateInvestmentAIReport, getMemberDashboard, saveCardFeedback }));

vi.mock("../shared/analytics/events", () => ({ trackEvent }));

const dashboard: MemberDashboard = {
  member_id: "LEO",
  display_name: "LEO",
  report: {
    report_id: "report-1",
    persona_code: "LHC",
    persona_name: "深潛集中者",
    persona_headline: "看得深，也抱得住。",
    confidence: 88,
    average_return: 14.2,
    scores: { outcome: 24, entry: 22, capture: 25, data: 17 },
    narrative: {
      headline: "歷史報告",
      summary: "已驗證的敘事。",
      insight: "只使用歷史資料。",
      source: "fallback",
    },
    created_at: "2026-07-15T00:00:00Z",
  },
  portfolio: [{
    stock_id: "2382",
    name: "廣達",
    industry: "電腦及週邊設備業",
    source: "user_confirmed",
    confirmed_at: "2026-07-15T00:00:00Z",
    shares: null,
    average_cost: null,
  }],
  priority_card: {
    card_id: "card-2382",
    stock_id: "2382",
    stock_name: "廣達",
    title: "法人與社群訊號出現背離",
    summary: "只整理可追溯證據。",
    as_of: "2025-12-31",
    provenance: "deterministic",
    narrative_source: "fallback",
    evidence: [{ label: "外資", value: "近 5 日賣超", tone: "warning" }],
    suggested_questions: ["資料日期是什麼時候？"],
    current_preference: null,
  },
  weekly_review: {
    title: "本週投資脈絡",
    summary: "一檔持股有新證據。",
    next_review_at: "2026-07-22T00:00:00Z",
    data_as_of: "2025-12-31",
    source: "snapshot",
  },
};

describe("PortfolioRadarRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    saveMemberSession("signed-session", "LEO");
    getMemberDashboard.mockResolvedValue(dashboard);
    saveCardFeedback.mockResolvedValue({ card_id: "card-2382", preference: "routine", saved_at: "2026-07-15T00:00:00Z" });
    generateInvestmentAIReport.mockResolvedValue({
      title: "LEO 的 Investment DNA 深度解讀",
      executive_summary: "這是歷史資料回顧。",
      strengths: [{ title: "代表成果", body: "廣達表現突出。", evidence_refs: ["trade:0"] }],
      watchouts: [{ title: "值得回看", body: "回看進場月份。", evidence_refs: ["trade:1"] }],
      market_moments: [],
      suggested_questions: [{ id: "why-persona", label: "為什麼我是這種投資人格？" }],
      source: "fallback",
      versions: { context: "v1" },
      generated_at: "2026-07-15T00:00:00Z",
    });
    askInvestmentQuestion.mockResolvedValue({
      question_id: "why-persona",
      answer: "來自五筆交易的綜合計分。",
      evidence_refs: ["trade:0"],
      limitations: "不構成投資建議。",
      source: "fallback",
      prompt_version: "investment-question-v1",
    });
  });

  it("unlocks structured AI deep dive and uses fixed question chips", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter><PortfolioRadarRoute /></MemoryRouter>
      </QueryClientProvider>,
    );

    fireEvent.click(await screen.findByRole("button", { name: "產生 AI 深度解讀" }));
    expect(await screen.findByText("LEO 的 Investment DNA 深度解讀")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "為什麼我是這種投資人格？" }));
    expect(await screen.findByText("來自五筆交易的綜合計分。")).toBeInTheDocument();
    expect(generateInvestmentAIReport).toHaveBeenCalledWith("report-1", "signed-session");
    expect(askInvestmentQuestion).toHaveBeenCalledWith("report-1", "why-persona", "signed-session");
  });

  afterEach(() => {
    cleanup();
  });

  it("renders the four retention modules from confirmed portfolio truth", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter><PortfolioRadarRoute /></MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: "你的 2025 投資人格" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "我的庫存" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "今日優先證據" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "本週投資脈絡" })).toBeInTheDocument();
    expect(screen.getByText("歷史資料・2025-12-31")).toBeInTheDocument();
    expect(screen.getByText("規則備援")).toBeInTheDocument();
    expect(screen.getByText("目前快照預覽")).toBeInTheDocument();
    expect(screen.getByText("本人確認")).toBeInTheDocument();
    expect(screen.getByText("成果")).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: "成果 24 分" })).toHaveAttribute("aria-valuemax", "40");
    expect(trackEvent).toHaveBeenCalledWith("action_card_impression", "portfolio_radar", { stock_id: "2382" });
  });

  it("supports evidence, contextual follow-up and one-tap feedback", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter><PortfolioRadarRoute /></MemoryRouter>
      </QueryClientProvider>,
    );

    const evidenceButton = await screen.findByRole("button", { name: /查看完整證據/ });
    fireEvent.click(evidenceButton);
    expect(screen.getByText("資料來源：deterministic・資料日期：2025-12-31")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "資料日期是什麼時候？" }));
    expect(screen.getByRole("status")).toHaveTextContent("這張卡使用 2025-12-31 的封存資料");

    fireEvent.click(screen.getByRole("button", { name: "只是例行查看" }));
    await waitFor(() => expect(saveCardFeedback).toHaveBeenCalledWith("card-2382", "routine", "signed-session"));
  });
});
