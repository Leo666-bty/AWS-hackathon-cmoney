const CONFIG = {
  userId: "LEO",
  stockId: "2382",
  cardId: "signal-divergence-2382",
  sourceDate: "2025-12-31",
  apiBaseUrl: "/api/v1",
  apiEnabled: false,
};

const STORAGE = {
  state: "mindfolio_mvp_state_v1",
  events: "mindfolio_event_history_v1",
  outbox: "mindfolio_event_outbox_v1",
  session: "mindfolio_session_id_v1",
};

const state = {
  page: "watchlist",
  stockTab: "aftermarket",
  relationship: null,
  concern: null,
  cardShownAt: null,
  cardImpressionSent: false,
  events: [],
  outbox: [],
  sessionId: "",
};

const pages = Object.fromEntries(
  [...document.querySelectorAll("[data-page]")].map((page) => [page.dataset.page, page]),
);

function createId() {
  return globalThis.crypto?.randomUUID?.() || `evt-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function readJson(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
}

function saveState() {
  localStorage.setItem(
    STORAGE.state,
    JSON.stringify({
      relationship: state.relationship,
      concern: state.concern,
      lastUpdated: new Date().toISOString(),
    }),
  );
  localStorage.setItem(STORAGE.events, JSON.stringify(state.events));
  localStorage.setItem(STORAGE.outbox, JSON.stringify(state.outbox));
}

function loadState() {
  const saved = readJson(STORAGE.state, {});
  state.relationship = saved.relationship || null;
  state.concern = saved.concern || null;
  state.events = readJson(STORAGE.events, []);
  state.outbox = readJson(STORAGE.outbox, []);
  state.sessionId = sessionStorage.getItem(STORAGE.session) || createId();
  sessionStorage.setItem(STORAGE.session, state.sessionId);
}

function eventSummary(event) {
  return event.action || event.metadata?.tab || event.metadata?.news_id || event.metadata?.evidence || "—";
}

function trackEvent(eventType, data = {}) {
  const event = {
    event_id: createId(),
    session_id: state.sessionId,
    event_type: eventType,
    user_id: CONFIG.userId,
    stock_id: Object.hasOwn(data, "stock_id") ? data.stock_id : CONFIG.stockId,
    card_id: Object.hasOwn(data, "card_id") ? data.card_id : CONFIG.cardId,
    surface: data.surface || state.page,
    action: data.action || null,
    occurred_at: new Date().toISOString(),
    source_date: CONFIG.sourceDate,
    metadata: data.metadata || {},
    sync_status: "queued",
  };

  state.events.unshift(event);
  state.events = state.events.slice(0, 100);
  state.outbox.push(event);
  saveState();
  renderDashboard();
  void flushOutbox();
  return event;
}

async function flushOutbox() {
  if (!CONFIG.apiEnabled || state.outbox.length === 0) {
    renderSyncStatus();
    return { queued: state.outbox.length };
  }

  const batch = [...state.outbox];
  try {
    const response = await fetch(`${CONFIG.apiBaseUrl}/events/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ events: batch }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = await response.json();
    const accepted = new Set(result.accepted_event_ids || batch.map((event) => event.event_id));
    state.outbox = state.outbox.filter((event) => !accepted.has(event.event_id));
    state.events.forEach((event) => {
      if (accepted.has(event.event_id)) event.sync_status = "synced";
    });
    saveState();
    renderDashboard();
    return { synced: accepted.size };
  } catch (error) {
    renderSyncStatus("API 暫時無法連線，事件保留於本機 outbox");
    return { queued: state.outbox.length, error: error.message };
  }
}

function showToast(message) {
  const toast = document.querySelector("#toast");
  toast.textContent = message;
  toast.classList.remove("hidden");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.add("hidden"), 2600);
}

function navigate(page, options = {}) {
  if (!pages[page]) return;
  const previous = state.page;
  state.page = page;
  Object.entries(pages).forEach(([key, element]) => element.classList.toggle("active", key === page));
  document.querySelectorAll(".nav").forEach((button) => {
    button.classList.toggle("active", button.dataset.pageLink === page);
  });

  if (options.track !== false && previous !== page) {
    const eventType = page === "stock" ? "stock_open" : page === "portfolio" ? "portfolio_view" : `${page}_view`;
    trackEvent(eventType, { surface: page, metadata: { from: previous } });
  }
  if (page === "stock") showCardImpression();
  if (page === "dashboard") renderDashboard();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function switchStockTab(tab, shouldTrack = true) {
  state.stockTab = tab;
  document.querySelectorAll(".stock-tab").forEach((button) => {
    button.classList.toggle("selected", button.dataset.stockTab === tab);
  });
  document.querySelectorAll("[data-tab-panel]").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.tabPanel === tab);
  });
  if (shouldTrack) trackEvent("stock_tab_view", { surface: "stock", metadata: { tab } });
}

function showCardImpression() {
  if (state.cardImpressionSent) return;
  state.cardImpressionSent = true;
  state.cardShownAt = Date.now();
  trackEvent("card_impression", {
    surface: "stock_insight",
    metadata: { card_type: "signal_divergence", title: "市場很樂觀，法人卻仍在調節" },
  });
}

function resultContent(relationship) {
  if (relationship === "holding") {
    return ["已確認持股", "廣達已加入你的庫存情境", "之後廣達的重大籌碼變化會優先出現在你的今日洞察。"];
  }
  if (relationship === "watch_only") {
    return ["已標記為觀察", "不會將廣達視為你的持股", "系統仍可顯示一般籌碼資訊，但不會使用持股語氣。"];
  }
  return ["已降低相關性", "已記住這張卡片與你無關", "類似廣達的提醒將降低顯示優先度。"];
}

function renderRelationship() {
  const hasFeedback = Boolean(state.relationship);
  document.querySelector("#discoveryState").classList.toggle("hidden", hasFeedback);
  document.querySelector("#resultState").classList.toggle("hidden", !hasFeedback);
  if (!hasFeedback) return;
  const [badge, title, copy] = resultContent(state.relationship);
  document.querySelector("#resultBadge").textContent = badge;
  document.querySelector("#resultTitle").textContent = title;
  document.querySelector("#resultCopy").textContent = copy;
}

function concernText(concern) {
  return {
    worried: "LEO 回覆：有點擔心。後續優先提供證據整理，不放大情緒。",
    routine: "LEO 回覆：只是例行查看。不提高提醒頻率。",
    mute: "LEO 回覆：不用提醒。已降低同類卡片優先度。",
  }[concern] || "尚未回覆目前感受";
}

function render() {
  renderRelationship();
  const confirmed = state.relationship === "holding";
  document.querySelector("#portfolioCount").textContent = confirmed ? "1" : "0";
  document.querySelector("#emptyPortfolio").classList.toggle("hidden", confirmed);
  document.querySelector("#holdingCard").classList.toggle("hidden", !confirmed);
  document.querySelector("#concernResult").textContent = concernText(state.concern);
  document.querySelector("#concernKnowledge").classList.toggle("known", Boolean(state.concern));
  document.querySelector("#concernKnowledge").textContent = state.concern ? "目前是否需要提醒" : "目前是否需要提醒（未知）";
  document.querySelectorAll("[data-concern]").forEach((button) => {
    button.classList.toggle("selected", button.dataset.concern === state.concern);
  });
  renderDashboard();
}

function respond(relationship) {
  const actionMap = {
    holding: "confirmed_holding",
    watch_only: "watch_only",
    irrelevant: "irrelevant",
  };
  state.relationship = relationship;
  trackEvent("relationship_feedback", {
    surface: "stock_insight",
    action: actionMap[relationship],
    metadata: { time_to_action_ms: state.cardShownAt ? Date.now() - state.cardShownAt : null },
  });
  saveState();
  render();
  showToast(relationship === "holding" ? "已加入 LEO 的庫存情境" : "已記住這次回饋");
}

function answerFollowup(type) {
  const answers = {
    divergence: "社群情緒反映市場敘事，法人籌碼反映資金行動，兩者時間尺度不同。這是值得確認的背離，不代表必然上漲或下跌。",
    portfolio: state.relationship === "holding"
      ? "廣達已由 LEO 確認為持股，所以同一訊號會提高優先級；目前沒有股數與成本，因此不計算損益或部位占比。"
      : "目前尚未確認廣達是持股，因此只提供一般市場解讀，不使用個人持股語氣。",
    evidence: "完整證據：近 20 日法人賣超 60,265 張、單日法人買超 3,957 張、近 7 日明確多空貼文 93.9% 看多。",
  };
  const answer = document.querySelector("#followupAnswer");
  answer.textContent = answers[type];
  answer.classList.remove("hidden");
  trackEvent("ai_followup_open", { surface: "stock_insight", action: type });
}

function setConcern(concern) {
  state.concern = concern;
  trackEvent("concern_feedback", { surface: "stock_insight", action: concern });
  saveState();
  render();
  showToast("已記住你的提醒偏好");
}

function renderSyncStatus(override) {
  const status = document.querySelector("#syncStatus");
  if (!status) return;
  status.textContent = override || (state.outbox.length ? `Local outbox · ${state.outbox.length} 待同步` : "事件已同步");
}

function renderDashboard() {
  const count = (type) => state.events.filter((event) => event.event_type === type).length;
  document.querySelector("#metricEvents").textContent = state.events.length;
  document.querySelector("#metricImpressions").textContent = count("card_impression");
  document.querySelector("#metricFeedback").textContent = count("relationship_feedback");
  document.querySelector("#metricHoldings").textContent = state.relationship === "holding" ? "1" : "0";
  renderSyncStatus();

  const table = document.querySelector("#eventTable");
  if (!state.events.length) {
    table.innerHTML = '<p class="empty-events">尚未產生事件。</p>';
    return;
  }
  table.innerHTML = `
    <div class="event-row event-head"><span>時間</span><span>事件</span><span>內容</span><span>狀態</span></div>
    ${state.events.slice(0, 15).map((event) => `
      <div class="event-row">
        <span>${new Date(event.occurred_at).toLocaleTimeString("zh-TW", { hour12: false })}</span>
        <b>${event.event_type}</b>
        <span>${eventSummary(event)}</span>
        <em>${event.sync_status === "synced" ? "synced" : "queued"}</em>
      </div>`).join("")}
  `;
}

function removeHolding() {
  state.relationship = null;
  state.concern = null;
  trackEvent("holding_removed", { surface: "portfolio", action: "removed" });
  saveState();
  render();
  showToast("已移除廣達持股關係");
}

function resetDemo() {
  [STORAGE.state, STORAGE.events, STORAGE.outbox].forEach((key) => localStorage.removeItem(key));
  sessionStorage.removeItem(STORAGE.session);
  window.location.reload();
}

function bindEvents() {
  document.querySelectorAll("[data-page-link]").forEach((button) => {
    button.addEventListener("click", () => navigate(button.dataset.pageLink));
  });
  document.querySelector("#openQuantaBtn").addEventListener("click", () => navigate("stock"));
  document.querySelectorAll(".stock-tab").forEach((button) => {
    button.addEventListener("click", () => switchStockTab(button.dataset.stockTab));
  });
  document.querySelectorAll(".evidence-button").forEach((button) => {
    button.addEventListener("click", () => {
      trackEvent("card_evidence_open", { surface: `stock_${state.stockTab}`, metadata: { evidence: button.dataset.evidence } });
      document.querySelector("#relationshipBlock").classList.remove("hidden");
      showToast("證據已記錄，可用一鍵回饋補全關係");
    });
  });
  document.querySelector("#expandEvidenceBtn").addEventListener("click", () => {
    document.querySelector("#relationshipBlock").classList.remove("hidden");
    trackEvent("card_evidence_open", { surface: "stock_insight", metadata: { evidence: "summary" } });
  });
  document.querySelector("#holdingBtn").addEventListener("click", () => respond("holding"));
  document.querySelector("#watchBtn").addEventListener("click", () => respond("watch_only"));
  document.querySelector("#irrelevantBtn").addEventListener("click", () => respond("irrelevant"));
  document.querySelectorAll("[data-followup]").forEach((button) => {
    button.addEventListener("click", () => answerFollowup(button.dataset.followup));
  });
  document.querySelectorAll("[data-concern]").forEach((button) => {
    button.addEventListener("click", () => setConcern(button.dataset.concern));
  });
  document.querySelectorAll("[data-news-id]").forEach((button) => {
    button.addEventListener("click", () => {
      button.classList.toggle("opened");
      trackEvent("news_open", { surface: "stock_news", metadata: { news_id: button.dataset.newsId } });
    });
  });
  document.querySelector("#removeBtn").addEventListener("click", removeHolding);
  document.querySelector("#resetBtn").addEventListener("click", resetDemo);
  document.querySelector("#retrySyncBtn").addEventListener("click", () => void flushOutbox());
}

function init() {
  loadState();
  bindEvents();
  navigate("watchlist", { track: false });
  switchStockTab(state.stockTab, false);
  render();
  trackEvent("watchlist_view", { surface: "watchlist", stock_id: null, card_id: null });
}

init();
