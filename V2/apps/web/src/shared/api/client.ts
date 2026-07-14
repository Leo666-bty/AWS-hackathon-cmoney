import { z } from "zod";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api/v2";

const healthSchema = z.object({
  status: z.literal("ok"),
  service: z.string(),
  version: z.string(),
  model_status: z.string(),
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
});

const completeResponseSchema = z.object({
  result: reconstructionResultSchema,
  narrative: narrativeSchema,
});

const confirmedHoldingSchema = z.object({
  user_id: z.string(),
  stock_id: z.string(),
  source: z.literal("user_confirmed"),
  confirmed_at: z.string(),
});

const errorSchema = z.object({ detail: z.unknown().optional() });

export type HealthResponse = z.infer<typeof healthSchema>;
export type StockSummary = z.infer<typeof stockSchema>;
export type MonthEnvelope = z.infer<typeof monthEnvelopeSchema>;
export type PriceValidation = z.infer<typeof validationSchema>;
export type CompleteResponse = z.infer<typeof completeResponseSchema>;
export type ConfirmedHolding = z.infer<typeof confirmedHoldingSchema>;

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
