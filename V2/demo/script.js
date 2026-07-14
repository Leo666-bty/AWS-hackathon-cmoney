const database = MARKET_DATABASE;
const stockMap = new Map(database.stocks.map((stock) => [stock.id, stock]));
const monthLabels = {"01":"1 月","02":"2 月","03":"3 月","04":"4 月","05":"5 月","06":"6 月","07":"7 月","08":"8 月","09":"9 月","10":"10 月","11":"11 月","12":"12 月"};
const allMonths = Object.keys(monthLabels);

const screens = {
  hero: document.querySelector("#heroScreen"),
  builder: document.querySelector("#builderScreen"),
  configure: document.querySelector("#configureScreen"),
  computing: document.querySelector("#computingScreen"),
  result: document.querySelector("#resultScreen"),
};

const state = { selected: [], configIndex: 0, configs: {}, result: null };

const personaMap = {
  LHD:["低接收藏家","你偏好在月內相對低位建立部位，並用較長時間與分散配置等待價值展開。"],
  LHC:["深潛集中派","你願意在價格回落時集中研究少數主題，並以長期持有驗證判斷。"],
  LAD:["低點輪動者","你喜歡在相對低位進場，再依月份節奏主動調整不同產業部位。"],
  LAC:["逆勢狙擊手","你在回落時聚焦少數機會，也會主動尋找離場月份。"],
  THD:["趨勢配置師","你偏好價格確認後進場，並用多產業配置讓趨勢持續發展。"],
  THC:["主題領航員","你會在主題與價格同步後集中投入，並給核心部位更長的驗證時間。"],
  TAD:["動能輪動者","你跟隨市場方向，也會在不同產業與月份之間主動輪動。"],
  TAC:["趨勢突擊手","你重視方向確認、主題集中與明確的進出節奏。"],
};

function track(eventType, metadata = {}) {
  const key = "mindfolio_v2_reconstruction_events";
  let events = [];
  try { events = JSON.parse(localStorage.getItem(key) || "[]"); } catch { events = []; }
  events.push({ event_type: eventType, occurred_at: new Date().toISOString(), metadata });
  try { localStorage.setItem(key, JSON.stringify(events.slice(-150))); } catch { /* local demo fallback */ }
}

function showScreen(name) {
  Object.entries(screens).forEach(([key, node]) => node.classList.toggle("active", key === name));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function reset() {
  state.selected = [];
  state.configIndex = 0;
  state.configs = {};
  state.result = null;
  document.querySelector("#stockSearch").value = "";
  renderStockResults();
  renderSelected();
  showScreen("hero");
}

function showToast(message) {
  const toast = document.querySelector("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("show"), 2800);
}

function formatPrice(value) {
  return Number(value).toLocaleString("zh-TW", { minimumFractionDigits: value < 100 ? 2 : 1, maximumFractionDigits: 2 });
}

function formatReturn(value) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`;
}

function renderStockResults() {
  const query = document.querySelector("#stockSearch").value.trim().toLowerCase();
  const popularRank = new Map(database.popular.map((id, index) => [id, index]));
  let results = database.stocks.filter((stock) => {
    if (!query) return stock.popular;
    return `${stock.id} ${stock.name} ${stock.industry}`.toLowerCase().includes(query);
  });
  results.sort((a, b) => query ? b.views - a.views : (popularRank.get(a.id) ?? 99) - (popularRank.get(b.id) ?? 99));
  results = results.slice(0, query ? 16 : 12);
  const container = document.querySelector("#stockResults");
  container.innerHTML = results.map((stock) => {
    const selected = state.selected.includes(stock.id);
    return `<button class="stock-option ${selected ? "selected" : ""}" data-stock-id="${stock.id}">
      <i>${stock.id}</i><span><b>${stock.name}</b><small>${stock.industry} · ${stock.views.toLocaleString()} 人瀏覽</small></span><span>${selected ? "✓" : "+"}</span>
    </button>`;
  }).join("") || '<p class="validation warn">找不到符合的股票，請改用代號或名稱搜尋。</p>';
  container.querySelectorAll("[data-stock-id]").forEach((button) => button.addEventListener("click", () => toggleStock(button.dataset.stockId)));
}

function toggleStock(stockId) {
  const existing = state.selected.indexOf(stockId);
  if (existing >= 0) state.selected.splice(existing, 1);
  else if (state.selected.length < 5) state.selected.push(stockId);
  else return showToast("最多選擇五檔，請先移除一檔");
  renderStockResults();
  renderSelected();
}

function renderSelected() {
  document.querySelector("#selectedCount").textContent = `${state.selected.length} / 5`;
  const slots = [...state.selected.map((id) => ({ stock: stockMap.get(id) })), ...Array.from({ length: 5 - state.selected.length }, () => ({ stock: null }))];
  const container = document.querySelector("#selectedList");
  container.innerHTML = slots.map(({ stock }, index) => stock
    ? `<div class="selected-stock"><b>${stock.id} ${stock.name}<small>${stock.industry}</small></b><button data-remove="${stock.id}" aria-label="移除 ${stock.name}">×</button></div>`
    : `<div class="empty-slot">第 ${index + 1} 檔等待選擇</div>`).join("");
  container.querySelectorAll("[data-remove]").forEach((button) => button.addEventListener("click", () => toggleStock(button.dataset.remove)));
  document.querySelector("#configureBtn").disabled = state.selected.length !== 5;
}

function defaultConfig(stock) {
  const firstMonth = allMonths.find((month) => stock.months[month]);
  return { relation: "holding", buyMonth: firstMonth || "01", buyMode: "band", buyBand: "mid", buyExact: "", sellMonth: "12", sellMode: "estimate", sellExact: "" };
}

function beginConfiguration() {
  if (state.selected.length !== 5) return;
  state.configIndex = 0;
  state.selected.forEach((id) => { if (!state.configs[id]) state.configs[id] = defaultConfig(stockMap.get(id)); });
  track("portfolio_selection_complete", { stock_ids: [...state.selected] });
  showScreen("configure");
  renderConfiguration();
}

function priceAtBand(monthData, band) {
  const spread = monthData.high - monthData.low;
  return { low: monthData.low + spread / 6, mid: monthData.low + spread / 2, high: monthData.low + spread * 5 / 6 }[band];
}

function bandOptions(monthData, activeBand) {
  return [["low","偏低區"],["mid","中間區"],["high","偏高區"]].map(([band, label]) => {
    const value = priceAtBand(monthData, band);
    return `<button class="${activeBand === band ? "active" : ""}" data-buy-band="${band}"><b>${label}</b><small>約 ${formatPrice(value)}</small></button>`;
  }).join("");
}

function validateExact(value, monthData) {
  const price = Number(value);
  if (!value || !Number.isFinite(price) || price <= 0) return { valid: false, level: "bad", message: "請輸入大於 0 的成交價格。" };
  if (price < monthData.low || price > monthData.high) return { valid: false, level: "bad", message: `超出該月行情 ${formatPrice(monthData.low)}–${formatPrice(monthData.high)}，請確認月份或改用價格區間。` };
  if (monthData.corporateAction) {
    const regime = monthData.regimes?.find((item) => price >= item.low && price <= item.high);
    if (!regime) return { valid: false, level: "bad", message: `該月有公司行動，價格必須落在實際交易區段：${monthData.regimes.map((item) => `${formatPrice(item.low)}–${formatPrice(item.high)}`).join(" 或 ")}。` };
    return { valid: true, level: "warn", message: `價格符合 ${formatPrice(regime.low)}–${formatPrice(regime.high)} 區段，報酬會用對應還原因子校正。` };
  }
  return { valid: true, level: "good", message: `通過行情驗證：落在 ${formatPrice(monthData.low)}–${formatPrice(monthData.high)}。` };
}

function factorForRawPrice(monthData, rawPrice) {
  const matchingRegime = monthData.regimes?.find((regime) => rawPrice >= regime.low && rawPrice <= regime.high);
  return matchingRegime?.factor ?? monthData.factor;
}

function validSellMonths(stock, buyMonth) {
  return allMonths.filter((month) => Number(month) > Number(buyMonth) && stock.months[month]);
}

function normalizeConfig(config, stock) {
  if (!stock.months[config.buyMonth]) config.buyMonth = allMonths.find((month) => stock.months[month]);
  const sellMonths = validSellMonths(stock, config.buyMonth);
  if (!sellMonths.includes(config.sellMonth)) config.sellMonth = sellMonths.at(-1) || "12";
  if (!sellMonths.length) config.relation = "holding";
}

function monthChart(stock, config) {
  const values = Object.values(stock.months).map((month) => month.adjustedClose);
  const min = Math.min(...values), max = Math.max(...values);
  return allMonths.map((month) => {
    const data = stock.months[month];
    if (!data) return `<div class="month-bar"><i style="height:5%"></i><small>${month}</small></div>`;
    const height = 18 + ((data.adjustedClose - min) / Math.max(max - min, .0001)) * 78;
    const active = month === config.buyMonth || (config.relation === "sold" && month === config.sellMonth) || (config.relation === "holding" && month === "12");
    return `<div class="month-bar ${active ? "active" : ""}"><i style="height:${height}%"></i><small>${month}</small></div>`;
  }).join("");
}

function renderConfiguration() {
  const stockId = state.selected[state.configIndex];
  const stock = stockMap.get(stockId);
  const config = state.configs[stockId];
  normalizeConfig(config, stock);
  const buyData = stock.months[config.buyMonth];
  const sellData = stock.months[config.sellMonth];
  const buyValidation = config.buyMode === "exact" ? validateExact(config.buyExact, buyData) : { valid: !buyData.corporateAction, level: buyData.corporateAction ? "bad" : "good", message: buyData.corporateAction ? "該月發生拆分或公司行動，單一價格區間會失真；請輸入實際價格或改選月份。" : `將以 ${monthLabels[config.buyMonth]}價格區間中點估算。` };
  const sellValidation = config.sellMode === "exact" && config.relation === "sold" ? validateExact(config.sellExact, sellData) : { valid: true, level: "good", message: "" };
  const valid = buyValidation.valid && sellValidation.valid;
  document.querySelector("#configStep").textContent = `STEP 2 / 3 · STOCK ${state.configIndex + 1} / 5`;
  document.querySelector("#configTitle").textContent = `設定 ${stock.id} ${stock.name}`;
  document.querySelector("#configSubtitle").textContent = "只需大約月份與價格；手動價格會經過當月行情合理性檢查。";
  document.querySelector("#configProgress").style.width = `${((state.configIndex + 1) / 5) * 100}%`;

  const monthOptions = allMonths.filter((month) => stock.months[month]).map((month) => `<option value="${month}" ${month === config.buyMonth ? "selected" : ""}>2025 ${monthLabels[month]}</option>`).join("");
  const sellOptions = validSellMonths(stock, config.buyMonth).map((month) => `<option value="${month}" ${month === config.sellMonth ? "selected" : ""}>2025 ${monthLabels[month]}</option>`).join("");
  document.querySelector("#configContent").innerHTML = `
    <article class="config-card">
      <aside class="stock-context"><span>${stock.id}</span><h2>${stock.name}</h2><p>${stock.industry}</p><div class="month-chart">${monthChart(stock, config)}</div><footer>圖表使用公司行動調整後月末價格；表單中的價格範圍則是使用者當時會看到的原始行情。</footer></aside>
      <div class="config-form">
        <section class="form-section"><header><h3>① 2025 年底仍持有嗎？</h3><span>用來收集主動確認的持股關係</span></header><div class="segmented"><button data-relation="holding" class="${config.relation === "holding" ? "active" : ""}">仍持有至 12/31</button><button data-relation="sold" class="${config.relation === "sold" ? "active" : ""}" ${validSellMonths(stock, config.buyMonth).length ? "" : "disabled"}>已在 2025 賣出</button></div></section>
        <section class="form-section"><header><h3>② 大約何時買進？</h3><span>月份級即可</span></header><div class="field"><label>買進月份</label><select id="buyMonth">${monthOptions}</select></div><div class="price-mode"><button data-buy-mode="band" class="${config.buyMode === "band" ? "active" : ""}">選擇大致區間</button><button data-buy-mode="exact" class="${config.buyMode === "exact" ? "active" : ""}">輸入實際價格</button></div>${config.buyMode === "band" ? `<div class="band-options">${bandOptions(buyData, config.buyBand)}</div>` : `<div class="exact-row"><input id="buyExact" inputmode="decimal" placeholder="例如 ${formatPrice((buyData.low + buyData.high) / 2)}" value="${config.buyExact}" /><button class="secondary" id="checkBuy">檢查價格</button></div>`}<p class="validation ${buyValidation.level}">${buyValidation.message}</p></section>
        <section class="form-section"><header><h3>③ ${config.relation === "holding" ? "持有至資料基準日" : "大約何時賣出？"}</h3><span>${config.relation === "holding" ? "2025-12-31" : "月份級估算"}</span></header>${config.relation === "holding" ? `<div class="estimate-box">系統以 12 月最後交易日還原收盤價 <b>${formatPrice(stock.months["12"].adjustedClose)}</b> 計算。</div>` : `<div class="field-grid"><div class="field"><label>賣出月份</label><select id="sellMonth">${sellOptions}</select></div><div class="field"><label>賣出價格</label><select id="sellMode"><option value="estimate" ${config.sellMode === "estimate" ? "selected" : ""}>用該月收盤估算</option><option value="exact" ${config.sellMode === "exact" ? "selected" : ""}>輸入實際價格</option></select></div></div>${config.sellMode === "exact" ? `<div class="exact-row" style="margin-top:10px"><input id="sellExact" inputmode="decimal" placeholder="該月行情 ${formatPrice(sellData.low)}–${formatPrice(sellData.high)}" value="${config.sellExact}" /><button class="secondary" id="checkSell">檢查價格</button></div><p class="validation ${sellValidation.level}">${sellValidation.message}</p>` : `<p class="validation good">將使用 ${monthLabels[config.sellMonth]}最後交易日價格估算。</p>`}`}</section>
        <div class="config-next"><span>${valid ? "資料可進入重建引擎" : "請先修正異常價格"}</span><button class="primary" id="saveConfig" ${valid ? "" : "disabled"}>${state.configIndex === 4 ? "計算投資人格與報酬" : "儲存並設定下一檔"} →</button></div>
      </div>
    </article>`;
  bindConfigEvents(stock, config);
}

function bindConfigEvents(stock, config) {
  document.querySelectorAll("[data-relation]").forEach((button) => button.addEventListener("click", () => { config.relation = button.dataset.relation; renderConfiguration(); }));
  document.querySelector("#buyMonth").addEventListener("change", (event) => { config.buyMonth = event.target.value; normalizeConfig(config, stock); renderConfiguration(); });
  document.querySelectorAll("[data-buy-mode]").forEach((button) => button.addEventListener("click", () => { config.buyMode = button.dataset.buyMode; renderConfiguration(); }));
  document.querySelectorAll("[data-buy-band]").forEach((button) => button.addEventListener("click", () => { config.buyBand = button.dataset.buyBand; renderConfiguration(); }));
  document.querySelector("#buyExact")?.addEventListener("input", (event) => { config.buyExact = event.target.value; });
  document.querySelector("#checkBuy")?.addEventListener("click", renderConfiguration);
  document.querySelector("#sellMonth")?.addEventListener("change", (event) => { config.sellMonth = event.target.value; renderConfiguration(); });
  document.querySelector("#sellMode")?.addEventListener("change", (event) => { config.sellMode = event.target.value; renderConfiguration(); });
  document.querySelector("#sellExact")?.addEventListener("input", (event) => { config.sellExact = event.target.value; });
  document.querySelector("#checkSell")?.addEventListener("click", renderConfiguration);
  document.querySelector("#saveConfig").addEventListener("click", saveConfig);
}

function configValues(stock, config) {
  const buyData = stock.months[config.buyMonth];
  const exitMonth = config.relation === "holding" ? "12" : config.sellMonth;
  const exitData = stock.months[exitMonth];
  const buyRaw = config.buyMode === "exact" ? Number(config.buyExact) : priceAtBand(buyData, config.buyBand);
  const exitRaw = config.relation === "sold" && config.sellMode === "exact" ? Number(config.sellExact) : exitData.close;
  const buyAdjusted = buyRaw * factorForRawPrice(buyData, buyRaw);
  const exitAdjusted = config.relation === "holding" || config.sellMode === "estimate" ? exitData.adjustedClose : exitRaw * factorForRawPrice(exitData, exitRaw);
  const entryPosition = (buyRaw - buyData.low) / Math.max(buyData.high - buyData.low, .0001);
  const duration = Number(exitMonth) - Number(config.buyMonth);
  let confidence = config.buyMode === "exact" ? 100 : 78;
  if (config.relation === "sold" && config.sellMode === "estimate") confidence -= 8;
  if (config.relation === "sold" && config.sellMode === "exact") confidence = (confidence + 100) / 2;
  if (buyData.corporateAction || exitData.corporateAction) confidence -= 15;
  return { buyRaw, exitRaw, buyAdjusted, exitAdjusted, exitMonth, entryPosition, duration, confidence: Math.max(45, Math.round(confidence)), return: (exitAdjusted / buyAdjusted - 1) * 100 };
}

function saveConfig() {
  const stockId = state.selected[state.configIndex];
  const stock = stockMap.get(stockId);
  const config = state.configs[stockId];
  const buyValid = config.buyMode === "exact" ? validateExact(config.buyExact, stock.months[config.buyMonth]).valid : !stock.months[config.buyMonth].corporateAction;
  const sellValid = config.relation !== "sold" || config.sellMode !== "exact" || validateExact(config.sellExact, stock.months[config.sellMonth]).valid;
  if (!buyValid || !sellValid) {
    renderConfiguration();
    showToast("價格未通過該月行情驗證，請先修正");
    return;
  }
  const values = configValues(stock, config);
  track("holding_reconstruction_saved", { stock_id: stockId, relation: config.relation, buy_month: config.buyMonth, exit_month: values.exitMonth, price_mode: config.buyMode, confidence: values.confidence });
  if (state.configIndex < 4) { state.configIndex += 1; renderConfiguration(); window.scrollTo({ top: 0, behavior: "smooth" }); }
  else computeResult();
}

function clamp(value, min, max) { return Math.min(max, Math.max(min, value)); }

function computeResultData() {
  const trades = state.selected.map((id) => {
    const stock = stockMap.get(id), config = state.configs[id], values = configValues(stock, config);
    return { stock, config, ...values };
  });
  const averageReturn = trades.reduce((sum, trade) => sum + trade.return, 0) / trades.length;
  const entryAverage = trades.reduce((sum, trade) => sum + clamp(trade.entryPosition, 0, 1), 0) / trades.length;
  const durationAverage = trades.reduce((sum, trade) => sum + trade.duration / 11, 0) / trades.length;
  const holdings = trades.filter((trade) => trade.config.relation === "holding");
  const industryCounts = trades.reduce((counts, trade) => ({ ...counts, [trade.stock.industry]: (counts[trade.stock.industry] || 0) + 1 }), {});
  const concentration = Object.values(industryCounts).reduce((sum, count) => sum + (count / 5) ** 2, 0);
  const diversity = 1 - concentration;
  const exactRatio = trades.filter((trade) => trade.config.buyMode === "exact").length / trades.length;
  const confidence = Math.round(trades.reduce((sum, trade) => sum + trade.confidence, 0) / trades.length);
  const codePrefix = `${entryAverage <= .5 ? "L" : "T"}${holdings.length >= 3 || durationAverage >= .55 ? "H" : "A"}${diversity >= .65 ? "D" : "C"}`;
  const precisionCode = exactRatio >= .5 ? "X" : "E";
  const [persona, headline] = personaMap[codePrefix];
  const personaCopy = precisionCode === "X" ? "你提供較多可驗證的實際價格，投資指紋更接近個人交易軌跡。" : "你用月份與價格區間快速完成重建，適合再用一兩筆實際價格提升精準度。";
  const outcomeScore = clamp(Math.round(20 + averageReturn * .45), 0, 40);
  const entryScore = Math.round((1 - entryAverage) * 25);
  const captureScores = trades.map((trade) => {
    const future = allMonths.filter((month) => Number(month) > Number(trade.config.buyMonth) && trade.stock.months[month]).map((month) => trade.stock.months[month].adjustedClose);
    if (!future.length) return 10;
    const min = Math.min(...future), max = Math.max(...future);
    return 6 + ((trade.exitAdjusted - min) / Math.max(max - min, .0001)) * 14;
  });
  const captureScore = Math.round(clamp(captureScores.reduce((a, b) => a + b, 0) / captureScores.length, 0, 20));
  const dataScore = Math.round(confidence / 100 * 15);
  return { trades, averageReturn, holdings, confidence, code: `${codePrefix}${precisionCode}`, persona, headline, personaCopy, vector: [entryAverage, durationAverage, diversity, exactRatio, clamp((averageReturn + 50) / 150, 0, 1)], scores: { outcomeScore, entryScore, captureScore, dataScore } };
}

function computeResult() {
  showScreen("computing");
  const messages = ["驗證每筆價格是否落在當月行情…","套用拆股與除權息還原因子…","重建五檔買賣事件與投報率…","生成 Portfolio Fingerprint…"];
  let index = 0;
  document.querySelector("#computeMessage").textContent = messages[0];
  const timer = setInterval(() => { index += 1; if (index < messages.length) document.querySelector("#computeMessage").textContent = messages[index]; }, 420);
  setTimeout(() => { clearInterval(timer); state.result = computeResultData(); renderResult(); showScreen("result"); track("reconstruction_result_view", { code: state.result.code, confirmed_holdings: state.result.holdings.length, confidence: state.result.confidence }); }, 1750);
}

function renderResult() {
  const result = state.result;
  document.querySelector("#personaCode").textContent = result.code;
  document.querySelector("#personaName").textContent = result.persona;
  document.querySelector("#personaHeadline").textContent = result.headline;
  document.querySelector("#personaCopy").textContent = result.personaCopy;
  document.querySelector("#confidenceScore").textContent = result.confidence;
  const returnNode = document.querySelector("#portfolioReturn");
  returnNode.textContent = formatReturn(result.averageReturn);
  returnNode.className = result.averageReturn >= 0 ? "positive" : "negative";
  document.querySelector("#holdingCount").textContent = result.holdings.length;
  document.querySelector("#holdingNames").textContent = result.holdings.length ? result.holdings.map((trade) => `${trade.stock.id} ${trade.stock.name}`).join("、") : "這次沒有標記仍持有的股票";
  document.querySelector("#tradeTable").innerHTML = result.trades.map((trade) => `<div class="trade-row"><b>${trade.stock.id}<small>${trade.stock.name}</small></b><span>${monthLabels[trade.config.buyMonth]}買進 · ${formatPrice(trade.buyRaw)}</span><span>${monthLabels[trade.exitMonth]}${trade.config.relation === "holding" ? "持有" : "賣出"} · ${formatPrice(trade.exitRaw)}</span><em>${trade.confidence}%可信</em><strong class="${trade.return >= 0 ? "positive" : "negative"}">${formatReturn(trade.return)}</strong></div>`).join("");
  document.querySelector("#engineStatus").textContent = `${result.trades.length} / ${result.trades.length} validated`;
  document.querySelector("#fingerprintVector").textContent = `[${result.vector.map((value) => value.toFixed(2)).join(", ")}]`;
  const abilities = [["報酬結果",result.scores.outcomeScore,40,"五檔等權重重建報酬"],["進場位置",result.scores.entryScore,25,"成交價在當月區間的位置"],["報酬捕捉",result.scores.captureScore,20,"離場價相對後續月末價格"],["資料完整",result.scores.dataScore,15,"精確價格與行情驗證可信度"]];
  document.querySelector("#abilityGrid").innerHTML = abilities.map(([name,value,max,copy]) => `<article class="ability"><header><span>${name}</span><b>${value} / ${max}</b></header><i><b style="width:${value/max*100}%"></b></i><p>${copy}</p></article>`).join("");
  document.querySelector("#sharePersona").textContent = result.persona;
  document.querySelector("#shareCode").textContent = result.code;
  document.querySelector("#shareHeadline").textContent = result.headline;
}

async function share() {
  const text = `我的 2025 投資人格是「${state.result.persona} ${state.result.code}」！${state.result.headline} 不曬持股也能分享，你是哪一型？ #投資時光機 #Mindfolio`;
  track("share_copy", { code: state.result.code });
  try { await navigator.clipboard.writeText(text); showToast("匿名文案已複製，沒有包含持股與報酬明細"); }
  catch { window.prompt("複製匿名分享文案：", text); }
}

document.querySelector("#dbCount").textContent = database.stockCount;
document.querySelector("#envelopeCount").textContent = database.monthEnvelopeCount.toLocaleString();
document.querySelector("#startBtn").addEventListener("click", () => { showScreen("builder"); renderStockResults(); renderSelected(); track("portfolio_builder_start"); });
document.querySelector("#homeBtn").addEventListener("click", reset);
document.querySelectorAll("[data-reset]").forEach((button) => button.addEventListener("click", reset));
document.querySelector("#stockSearch").addEventListener("input", renderStockResults);
document.querySelector("#quickPickBtn").addEventListener("click", () => { state.selected = database.popular.slice(0, 5); renderStockResults(); renderSelected(); track("popular_five_selected", { stock_ids: [...state.selected] }); });
document.querySelector("#configureBtn").addEventListener("click", beginConfiguration);
document.querySelector("#shareBtn").addEventListener("click", share);
document.querySelector("#unlockBtn").addEventListener("click", () => { track("portfolio_radar_unlock_click", { confirmed_holdings: state.result.holdings.length }); showToast("Demo：下一步會徵求同意並儲存已確認持股，不會自動連結券商"); });

renderStockResults();
renderSelected();
