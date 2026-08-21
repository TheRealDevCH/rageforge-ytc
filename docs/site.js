(() => {
  const rows = Array.from(document.querySelectorAll(".format-row"));
  const echo = document.getElementById("formatEcho");
  const steps = Array.from(document.querySelectorAll(".flow-step"));
  const panels = Array.from(document.querySelectorAll(".flow-panel"));
  const drops = Array.from(document.querySelectorAll("[data-drop]"));
  const reveals = Array.from(document.querySelectorAll(".reveal"));

  const syncFormats = () => {
    const picked = rows
      .filter((row) => row.classList.contains("is-on"))
      .map((row) => row.dataset.fmt);
    if (echo) {
      echo.textContent = picked.length ? picked.join(" · ") : "Nichts gewählt";
    }
  };

  rows.forEach((row) => {
    row.addEventListener("click", () => {
      row.classList.toggle("is-on");
      row.setAttribute("aria-pressed", row.classList.contains("is-on") ? "true" : "false");
      syncFormats();
    });
  });

  const showStep = (index) => {
    steps.forEach((step, i) => {
      const on = i === index;
      step.classList.toggle("is-active", on);
      step.setAttribute("aria-pressed", on ? "true" : "false");
    });
    panels.forEach((panel) => {
      panel.classList.toggle("is-shown", Number(panel.dataset.panel) === index);
    });
  };

  steps.forEach((step) => {
    step.addEventListener("click", () => showStep(Number(step.dataset.step)));
  });

  drops.forEach((drop) => {
    const trigger = drop.querySelector("button");
    if (!trigger) return;
    trigger.addEventListener("click", (event) => {
      event.stopPropagation();
      const open = drop.classList.toggle("is-open");
      trigger.setAttribute("aria-expanded", open ? "true" : "false");
      drops.forEach((other) => {
        if (other === drop) return;
        other.classList.remove("is-open");
        const otherBtn = other.querySelector("button");
        if (otherBtn) otherBtn.setAttribute("aria-expanded", "false");
      });
    });
  });

  document.addEventListener("click", () => {
    drops.forEach((drop) => {
      drop.classList.remove("is-open");
      const trigger = drop.querySelector("button");
      if (trigger) trigger.setAttribute("aria-expanded", "false");
    });
  });

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.18, rootMargin: "0px 0px -8% 0px" }
    );
    reveals.forEach((node) => observer.observe(node));
  } else {
    reveals.forEach((node) => node.classList.add("is-in"));
  }

  syncFormats();
})();
