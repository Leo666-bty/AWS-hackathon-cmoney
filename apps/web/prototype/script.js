const state = { relationship: null, page: "stock" };

const pages = {
  stock: document.querySelector("#stockPage"),
  portfolio: document.querySelector("#portfolioPage"),
};

function navigate(page) {
  state.page = page;
  Object.entries(pages).forEach(([key, element]) => element.classList.toggle("active", key === page));
  document.querySelectorAll(".nav").forEach((button) => button.classList.toggle("active", button.dataset.page === page));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function render() {
  const confirmed = state.relationship === "holding";
  document.querySelector("#portfolioCount").textContent = confirmed ? "1" : "0";
  document.querySelector("#emptyPortfolio").classList.toggle("hidden", confirmed);
  document.querySelector("#holdingCard").classList.toggle("hidden", !confirmed);
}

function respond(type) {
  state.relationship = type;
  document.querySelector("#discoveryState").classList.add("hidden");
  document.querySelector("#resultState").classList.remove("hidden");

  const badge = document.querySelector("#resultBadge");
  const title = document.querySelector("#resultTitle");
  const copy = document.querySelector("#resultCopy");

  if (type === "holding") {
    badge.textContent = "已確認持股";
    title.textContent = "廣達已加入你的庫存情境";
    copy.textContent = "之後廣達的重大籌碼變化會優先出現在你的今日洞察。";
  } else if (type === "watch") {
    badge.textContent = "已標記為觀察";
    title.textContent = "不會將廣達視為你的持股";
    copy.textContent = "系統仍可顯示一般籌碼資訊，但不會使用持股語氣。";
  } else {
    badge.textContent = "已降低相關性";
    title.textContent = "已記住這張卡片與你無關";
    copy.textContent = "類似廣達的提醒將降低顯示優先度。";
  }
  render();
}

document.querySelectorAll("[data-page]").forEach((button) => button.addEventListener("click", (event) => {
  event.preventDefault();
  navigate(button.dataset.page);
}));
document.querySelector("#holdingBtn").addEventListener("click", () => respond("holding"));
document.querySelector("#watchBtn").addEventListener("click", () => respond("watch"));
document.querySelector("#irrelevantBtn").addEventListener("click", () => respond("irrelevant"));
document.querySelector("#removeBtn").addEventListener("click", () => window.location.reload());
document.querySelector("#resetBtn").addEventListener("click", () => window.location.reload());

render();
