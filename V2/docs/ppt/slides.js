(() => {
  "use strict";

  const slides = [...document.querySelectorAll(".slide")];
  const deck = document.querySelector("#deck");
  const progressBar = document.querySelector("#progressBar");
  const currentPage = document.querySelector("#currentPage");
  const sectionLabel = document.querySelector("#sectionLabel");
  const notesButton = document.querySelector("#notesButton");
  const overviewButton = document.querySelector("#overviewButton");
  const fullscreenButton = document.querySelector("#fullscreenButton");
  const slideDots = document.querySelector("#slideDots");
  const keyboardHelp = document.querySelector("#keyboardHelp");

  if (!deck || slides.length === 0) return;

  let activeIndex = 0;
  let touchStartX = null;

  const clamp = (value) => Math.max(0, Math.min(slides.length - 1, value));
  const pageFromHash = () => {
    const match = window.location.hash.match(/^#slide-(\d+)$/);
    return match ? clamp(Number(match[1]) - 1) : 0;
  };

  const updateChrome = () => {
    const slide = slides[activeIndex];
    const page = activeIndex + 1;
    currentPage.textContent = String(page).padStart(2, "0");
    sectionLabel.textContent = slide.dataset.title || "MINDFOLIO";
    progressBar.style.width = `${(page / slides.length) * 100}%`;
    slideDots?.querySelectorAll("button").forEach((dot, index) => {
      dot.classList.toggle("active", index === activeIndex);
      dot.setAttribute("aria-current", index === activeIndex ? "page" : "false");
    });
    document.title = `${String(page).padStart(2, "0")} · ${slide.dataset.title || "Mindfolio"}｜CMoney AI Hackathon`;
  };

  const showSlide = (index, updateHash = true) => {
    activeIndex = clamp(index);
    slides.forEach((slide, slideIndex) => {
      const active = slideIndex === activeIndex;
      slide.classList.toggle("is-active", active);
      slide.setAttribute("aria-hidden", String(!active));
    });
    if (updateHash) history.replaceState(null, "", `#slide-${activeIndex + 1}`);
    updateChrome();
  };

  const toggleNotes = () => {
    const enabled = document.body.classList.toggle("show-notes");
    notesButton.setAttribute("aria-pressed", String(enabled));
  };

  const setOverview = (enabled) => {
    document.body.classList.toggle("overview-mode", enabled);
    overviewButton.setAttribute("aria-pressed", String(enabled));
    slides.forEach((slide) => slide.setAttribute("aria-hidden", "false"));
    if (!enabled) showSlide(activeIndex, false);
  };

  const toggleOverview = () => setOverview(!document.body.classList.contains("overview-mode"));

  const toggleFullscreen = async () => {
    try {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
      else await document.exitFullscreen();
    } catch (error) {
      console.warn("Fullscreen is unavailable in this browser context.", error);
    }
  };

  const isInteractiveTarget = (target) => target instanceof HTMLElement && Boolean(target.closest("button, a, input, textarea, select"));

  document.addEventListener("keydown", (event) => {
    if (isInteractiveTarget(event.target)) return;
    const overview = document.body.classList.contains("overview-mode");
    switch (event.key.toLowerCase()) {
      case "arrowright":
      case "pagedown":
      case " ":
        if (!overview) showSlide(activeIndex + 1);
        event.preventDefault();
        break;
      case "arrowleft":
      case "pageup":
        if (!overview) showSlide(activeIndex - 1);
        event.preventDefault();
        break;
      case "home":
        setOverview(false);
        showSlide(0);
        event.preventDefault();
        break;
      case "end":
        setOverview(false);
        showSlide(slides.length - 1);
        event.preventDefault();
        break;
      case "n":
        toggleNotes();
        break;
      case "o":
        toggleOverview();
        break;
      case "f":
        void toggleFullscreen();
        break;
      case "escape":
        if (overview) setOverview(false);
        break;
      default:
        break;
    }
  });

  notesButton.addEventListener("click", toggleNotes);
  overviewButton.addEventListener("click", toggleOverview);
  fullscreenButton.addEventListener("click", () => void toggleFullscreen());

  slides.forEach((slide, index) => {
    slide.addEventListener("click", () => {
      if (!document.body.classList.contains("overview-mode")) return;
      activeIndex = index;
      setOverview(false);
      showSlide(index);
    });
  });

  if (slideDots) {
    slides.forEach((slide, index) => {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.title = `${String(index + 1).padStart(2, "0")} · ${slide.dataset.title || "投影片"}`;
      dot.setAttribute("aria-label", `前往第 ${index + 1} 頁：${slide.dataset.title || "投影片"}`);
      dot.addEventListener("click", () => showSlide(index));
      slideDots.append(dot);
    });
  }

  deck.addEventListener("touchstart", (event) => {
    touchStartX = event.changedTouches[0]?.clientX ?? null;
  }, { passive: true });

  deck.addEventListener("touchend", (event) => {
    if (touchStartX === null || document.body.classList.contains("overview-mode")) return;
    const endX = event.changedTouches[0]?.clientX ?? touchStartX;
    const delta = endX - touchStartX;
    if (Math.abs(delta) > 54) showSlide(activeIndex + (delta < 0 ? 1 : -1));
    touchStartX = null;
  }, { passive: true });

  window.addEventListener("hashchange", () => showSlide(pageFromHash(), false));
  document.addEventListener("fullscreenchange", () => {
    fullscreenButton.setAttribute("aria-pressed", String(Boolean(document.fullscreenElement)));
  });

  showSlide(pageFromHash(), false);

  if (keyboardHelp) {
    keyboardHelp.classList.add("visible");
    window.setTimeout(() => keyboardHelp.classList.remove("visible"), 2600);
  }
})();
