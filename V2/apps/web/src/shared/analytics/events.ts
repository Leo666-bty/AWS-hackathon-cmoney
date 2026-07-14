import { submitEventBatch, type InteractionEvent } from "../api/client";
import { getAccessToken } from "../auth/session";

const SESSION_KEY = "mindfolio_v2_session_id";
const OUTBOX_KEY = "mindfolio_v2_event_outbox";

function sessionId(): string {
  const existing = window.sessionStorage.getItem(SESSION_KEY);
  if (existing) return existing;
  const created = crypto.randomUUID();
  window.sessionStorage.setItem(SESSION_KEY, created);
  return created;
}

function readOutbox(): InteractionEvent[] {
  try {
    const parsed: unknown = JSON.parse(window.localStorage.getItem(OUTBOX_KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed as InteractionEvent[] : [];
  } catch {
    return [];
  }
}

function writeOutbox(events: InteractionEvent[]): void {
  window.localStorage.setItem(OUTBOX_KEY, JSON.stringify(events.slice(-100)));
}

export async function flushEvents(): Promise<void> {
  const queued = readOutbox();
  if (queued.length === 0) return;
  const response = await submitEventBatch(queued, getAccessToken() ?? undefined);
  const accepted = new Set(response.accepted_event_ids);
  writeOutbox(readOutbox().filter((event) => !accepted.has(event.event_id)));
}

export function trackEvent(
  eventType: string,
  surface: string,
  fields: Partial<Pick<InteractionEvent, "action" | "stock_id" | "metadata">> = {},
): void {
  const event: InteractionEvent = {
    event_id: crypto.randomUUID(),
    session_id: sessionId(),
    event_type: eventType,
    surface,
    occurred_at: new Date().toISOString(),
    metadata: fields.metadata ?? {},
    ...(fields.action ? { action: fields.action } : {}),
    ...(fields.stock_id ? { stock_id: fields.stock_id } : {}),
  };
  writeOutbox([...readOutbox(), event]);
  void flushEvents().catch(() => undefined);
}
