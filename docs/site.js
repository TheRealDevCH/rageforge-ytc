(() => {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const spotlight = document.getElementById("spotlight");
  const steps = Array.from(document.querySelectorAll(".flow-step"));
  const panels = Array.from(document.querySelectorAll(".stage-panel"));
  const formatHits = Array.from(document.querySelectorAll(".format-hit"));
  const formatEcho = document.getElementById("formatEcho");

  const setStep = (index) => {
    steps.forEach((step, i) => {
      const on = i === index;
      step.classList.toggle("is-active", on);
      step.setAttribute("aria-pressed", on ? "true" : "false");
    });
    panels.forEach((panel) => {
      panel.classList.toggle("is-visible", Number(panel.dataset.panel) === index);
    });
  };

  steps.forEach((step) => {
    step.addEventListener("click", () => setStep(Number(step.dataset.step)));
  });

  const syncFormats = () => {
    const selected = formatHits
      .filter((hit) => hit.classList.contains("is-on"))
      .map((hit) => hit.dataset.format);
    if (formatEcho) {
      formatEcho.textContent = selected.length
        ? `Gewählt: ${selected.join(", ")}`
        : "Noch nichts gewählt — tippe die Formate an.";
    }
  };

  formatHits.forEach((hit) => {
    hit.addEventListener("click", () => {
      hit.classList.toggle("is-on");
      hit.setAttribute("aria-pressed", hit.classList.contains("is-on") ? "true" : "false");
      syncFormats();
    });
  });

  if (!reduce && spotlight) {
    window.addEventListener("pointermove", (event) => {
      spotlight.style.left = `${event.clientX}px`;
      spotlight.style.top = `${event.clientY}px`;
    });
  }

  if (!reduce && "IntersectionObserver" in window) {
    const targets = document.querySelectorAll(".story-head, .flow, .stage-board, .promise-rail, .finale-inner");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.style.opacity = "1";
          entry.target.style.transform = "translateY(0)";
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.16 }
    );
    targets.forEach((el) => {
      el.style.opacity = "0";
      el.style.transform = "translateY(28px)";
      el.style.transition = "opacity 700ms ease, transform 700ms ease";
      observer.observe(el);
    });
  }

  syncFormats();
})();
