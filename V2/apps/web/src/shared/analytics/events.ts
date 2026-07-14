import { submitEventBatch, type InteractionEvent } from "../api/client";
import { getAccessToken } from "../auth/session";

const SESSION_KEY = "mindfolio_v2_session_id";
const OUTBOX_KEY = "mindfolio_v2_event_outbox";

export function createClientId(): string {
  const cryptoApi = globalThis.crypto;
  if (typeof cryptoApi?.randomUUID === "function") {
    return cryptoApi.randomUUID();
  }

  const bytes = new Uint8Array(16);
  if (typeof cryptoApi?.getRandomValues === "function") {
    cryptoApi.getRandomValues(bytes);
  } else {
    for (let index = 0; index < bytes.length; index += 1) {
      bytes[index] = Math.floor(Math.random() * 256);
    }
  }
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

function sessionId(): string {
  const existing = window.sessionStorage.getItem(SESSION_KEY);
  if (existing) return existing;
  const created = createClientId();
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
  try {
    const event: InteractionEvent = {
      event_id: createClientId(),
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
  } catch {
    // Analytics must never block report claiming, holding consent or dashboard navigation.
  }
}
