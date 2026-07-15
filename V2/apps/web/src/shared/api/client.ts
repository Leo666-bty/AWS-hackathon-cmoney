import { z } from "zod";

const configuredApiBaseUrl: unknown = import.meta.env.VITE_API_BASE_URL;
const apiBaseUrl = typeof configuredApiBaseUrl === "string" ? configuredApiBaseUrl : "/api/v2";

const healthSchema = z.object({
  status: z.literal("ok"),
  service: z.string(),
  version: z.string(),
  model_status: z.string(),
  narrative_status: z.string(),
});

const stockSchema = z.object({
  id: z.string(),
  name: z.string(),
  industry: z.string(),
  views: z.number().int().nonnegative(),
  popular: z.boolean(),
  available_months: z.array(z.string()),
});

const priceRegimeSchema = z.object({
  low: z.number(),
  high: z.number(),
  factor: z.number(),
});

const monthEnvelopeSchema = z.object({
  stock_id: z.string(),
  month: z.string(),
  raw_low: z.number(),
  raw_high: z.number(),
  close: z.number(),
  adjusted_close: z.number(),
  factor: z.number(),
  corporate_action: z.boolean(),
  regimes: z.array(priceRegimeSchema),
  allowed_price_modes: z.array(z.string()),
});

const validationSchema = z.object({
  valid: z.boolean(),
  level: z.string(),
  message: z.string(),
});

const tradeResultSchema = z.object({
  stock_id: z.string(),
  name: z.string(),
  industry: z.string(),
  buy_month: z.string(),
  exit_month: z.string(),
  relation: z.string(),
  buy_raw: z.number(),
  exit_raw: z.number(),
  return_pct: z.number(),
  confidence: z.number().int(),
});

const reconstructionResultSchema = z.object({
  trades: z.array(tradeResultSchema),
  average_return: z.number(),
  confidence: z.number().int(),
  persona_code: z.string(),
  persona_name: z.string(),
  persona_headline: z.string(),
  fingerprint: z.array(z.number()),
  scores: z.object({
    outcome: z.number().int(),
    entry: z.number().int(),
    capture: z.number().int(),
    data: z.number().int(),
  }),
  holding_candidates: z.array(z.string()),
});

const narrativeSchema = z.object({
  headline: z.string(),
  summary: z.string(),
  insight: z.string(),
  source: z.enum(["bedrock", "fallback"]).default("fallback"),
});

const reportHandleSchema = z.object({
  report_id: z.string(),
  claim_token: z.string(),
  expires_at: z.string(),
});

const completeResponseSchema = z.object({
  result: reconstructionResultSchema,
  narrative: narrativeSchema,
  report: reportHandleSchema.nullable(),
});

const confirmedHoldingSchema = z.object({
  user_id: z.string(),
  stock_id: z.string(),
  source: z.literal("user_confirmed"),
  confirmed_at: z.string(),
});

const sessionSchema = z.object({
  access_token: z.string(),
  token_type: z.literal("bearer"),
  member_id: z.string(),
  display_name: z.string(),
});

const claimSchema = z.object({
  report_id: z.string(),
  member_id: z.string(),
  claimed_at: z.string(),
  holding_candidates: z.array(z.string()),
});

const dashboardSchema = z.object({
  member_id: z.string(),
  display_name: z.string(),
  report: z.object({
    report_id: z.string(),
    persona_code: z.string(),
    persona_name: z.string(),
    persona_headline: z.string(),
    confidence: z.number().int(),
    average_return: z.number(),
    scores: z.object({ outcome: z.number(), entry: z.number(), capture: z.number(), data: z.number() }),
    narrative: narrativeSchema,
    created_at: z.string(),
  }).nullable(),
  portfolio: z.array(z.object({
    stock_id: z.string(),
    name: z.string(),
    industry: z.string(),
    source: z.string(),
    confirmed_at: z.string(),
    shares: z.null(),
    average_cost: z.null(),
  })),
  priority_card: z.object({
    card_id: z.string(),
    stock_id: z.string(),
    stock_name: z.string(),
    title: z.string(),
    summary: z.string(),
    as_of: z.string(),
    provenance: z.string(),
    narrative_source: z.enum(["bedrock", "fallback"]),
    evidence: z.array(z.object({
      label: z.string(),
      value: z.string(),
      tone: z.enum(["neutral", "positive", "warning"]),
    })),
    suggested_questions: z.array(z.string()),
    current_preference: z.string().nullable(),
  }).nullable(),
  weekly_review: z.object({
    title: z.string(),
    summary: z.string(),
    next_review_at: z.string(),
    data_as_of: z.string(),
    source: z.enum(["snapshot", "fixture"]),
  }),
});

const feedbackSchema = z.object({
  card_id: z.string(),
  preference: z.string(),
  saved_at: z.string(),
});

const eventBatchSchema = z.object({ accepted_event_ids: z.array(z.string()) });

const evidenceSectionSchema = z.object({
  title: z.string(),
  body: z.string(),
  evidence_refs: z.array(z.string()),
});

const questionIdSchema = z.enum(["why-persona", "most-influential-trade", "why-anomalous-month"]);

const investmentAIReportSchema = z.object({
  title: z.string(),
  executive_summary: z.string(),
  strengths: z.array(evidenceSectionSchema),
  watchouts: z.array(evidenceSectionSchema),
  market_moments: z.array(evidenceSectionSchema),
  suggested_questions: z.array(z.object({ id: questionIdSchema, label: z.string() })),
  source: z.enum(["bedrock", "fallback"]),
  versions: z.record(z.string(), z.string()),
  generated_at: z.string(),
});

const questionAnswerSchema = z.object({
  question_id: questionIdSchema,
  answer: z.string(),
  evidence_refs: z.array(z.string()),
  limitations: z.string(),
  source: z.enum(["bedrock", "fallback"]),
  prompt_version: z.string(),
});

const errorSchema = z.object({ detail: z.unknown().optional() });

export type HealthResponse = z.infer<typeof healthSchema>;
export type StockSummary = z.infer<typeof stockSchema>;
export type MonthEnvelope = z.infer<typeof monthEnvelopeSchema>;
export type PriceValidation = z.infer<typeof validationSchema>;
export type CompleteResponse = z.infer<typeof completeResponseSchema>;
export type ConfirmedHolding = z.infer<typeof confirmedHoldingSchema>;
export type SessionResponse = z.infer<typeof sessionSchema>;
export type ClaimResponse = z.infer<typeof claimSchema>;
export type MemberDashboard = z.infer<typeof dashboardSchema>;
export type InvestmentAIReport = z.infer<typeof investmentAIReportSchema>;
export type InvestmentQuestionId = z.infer<typeof questionIdSchema>;
export type InvestmentQuestionAnswer = z.infer<typeof questionAnswerSchema>;
export type CardPreference = "review_evidence" | "routine" | "mute";
export type InteractionEvent = {
  event_id: string;
  session_id: string;
  event_type: string;
  surface: string;
  action?: string;
  stock_id?: string;
  occurred_at: string;
  metadata: Record<string, unknown>;
};

export type TradeConfig = {
  stock_id: string;
  relation: "holding" | "sold";
  buy_month: string;
  buy_mode: "band" | "exact";
  buy_band: "low" | "mid" | "high";
  buy_exact: number | null;
  sell_month: string;
  sell_mode: "estimate" | "exact";
  sell_exact: number | null;
};

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  schema: z.ZodType<T>,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const parsed = errorSchema.safeParse(payload);
    throw new ApiError(
      `API request failed with ${response.status}`,
      response.status,
      parsed.success ? parsed.data.detail : payload,
    );
  }
  return schema.parse(payload);
}

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return request("/health", healthSchema, { signal });
}

export function getPopularStocks(limit = 12, signal?: AbortSignal): Promise<StockSummary[]> {
  return request(`/stocks/popular?limit=${limit}`, z.array(stockSchema), { signal });
}

export function searchStocks(query: string, signal?: AbortSignal): Promise<StockSummary[]> {
  const params = new URLSearchParams({ q: query, limit: "20" });
  return request(`/stocks/search?${params.toString()}`, z.array(stockSchema), { signal });
}

export function getMonthEnvelope(
  stockId: string,
  month: string,
  signal?: AbortSignal,
): Promise<MonthEnvelope> {
  return request(`/stocks/${stockId}/months/2025-${month}/envelope`, monthEnvelopeSchema, { signal });
}

export function validateTrade(trade: TradeConfig): Promise<PriceValidation> {
  return request("/reconstructions/validate", validationSchema, {
    method: "POST",
    body: JSON.stringify(trade),
  });
}

export function completeReconstruction(trades: TradeConfig[]): Promise<CompleteResponse> {
  return request("/reconstructions/complete", completeResponseSchema, {
    method: "POST",
    body: JSON.stringify({ trades }),
  });
}

export function confirmHoldings(
  userId: string,
  trades: TradeConfig[],
): Promise<ConfirmedHolding[]> {
  return request("/confirmed-holdings", z.array(confirmedHoldingSchema), {
    method: "POST",
    body: JSON.stringify({ user_id: userId, trades }),
  });
}

export function createMemberSession(inviteCode: string): Promise<SessionResponse> {
  return request("/auth/session", sessionSchema, {
    method: "POST",
    body: JSON.stringify({ invite_code: inviteCode }),
  });
}

export function claimReport(
  reportId: string,
  claimToken: string,
  accessToken: string,
): Promise<ClaimResponse> {
  return request(`/reports/${reportId}/claim`, claimSchema, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify({ claim_token: claimToken }),
  });
}

export function confirmReportHoldings(
  reportId: string,
  stockIds: string[],
  accessToken: string,
): Promise<ConfirmedHolding[]> {
  return request(`/reports/${reportId}/confirmed-holdings`, z.array(confirmedHoldingSchema), {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify({ stock_ids: stockIds }),
  });
}

export function getMemberDashboard(accessToken: string, signal?: AbortSignal): Promise<MemberDashboard> {
  return request("/me/dashboard", dashboardSchema, {
    signal,
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export function saveCardFeedback(
  cardId: string,
  preference: CardPreference,
  accessToken: string,
) {
  return request(`/me/action-cards/${cardId}/feedback`, feedbackSchema, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify({ preference }),
  });
}

export function submitEventBatch(events: InteractionEvent[], accessToken?: string) {
  return request("/events/batch", eventBatchSchema, {
    method: "POST",
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
    body: JSON.stringify({ events }),
  });
}

export function generateInvestmentAIReport(reportId: string, accessToken: string): Promise<InvestmentAIReport> {
  return request(`/reports/${reportId}/ai-report`, investmentAIReportSchema, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export function askInvestmentQuestion(
  reportId: string,
  questionId: InvestmentQuestionId,
  accessToken: string,
): Promise<InvestmentQuestionAnswer> {
  return request(`/reports/${reportId}/questions`, questionAnswerSchema, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify({ question_id: questionId }),
  });
}
