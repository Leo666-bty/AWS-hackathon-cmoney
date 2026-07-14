const slides = [...document.querySelectorAll(".slide")];
const current = document.querySelector("#current");
const total = document.querySelector("#total");
let index = 0;

total.textContent = String(slides.length);

function show(nextIndex) {
  index = Math.max(0, Math.min(slides.length - 1, nextIndex));
  slides.forEach((slide, slideIndex) => slide.classList.toggle("active", slideIndex === index));
  current.textContent = String(index + 1);
  window.location.hash = `slide-${index + 1}`;
}

document.querySelector("#prev").addEventListener("click", () => show(index - 1));
document.querySelector("#next").addEventListener("click", () => show(index + 1));
document.addEventListener("keydown", (event) => {
  if (["ArrowRight", "PageDown", " "].includes(event.key)) show(index + 1);
  if (["ArrowLeft", "PageUp"].includes(event.key)) show(index - 1);
  if (event.key === "Home") show(0);
  if (event.key === "End") show(slides.length - 1);
});

const hashIndex = Number(window.location.hash.replace("#slide-", "")) - 1;
show(Number.isInteger(hashIndex) && hashIndex >= 0 ? hashIndex : 0);
