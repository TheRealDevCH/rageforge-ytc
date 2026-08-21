(() => {
  const orbs = Array.from(document.querySelectorAll(".orb"));
  const echo = document.getElementById("orbitEcho");
  const lanes = Array.from(document.querySelectorAll(".lane"));
  const panes = Array.from(document.querySelectorAll(".lens-pane"));
  const drops = Array.from(document.querySelectorAll("[data-drop]"));

  const syncOrbit = () => {
    const picked = orbs.filter((orb) => orb.classList.contains("is-live")).map((orb) => orb.dataset.fmt);
    if (echo) {
      echo.textContent = picked.length ? `Auswahl: ${picked.join(" · ")}` : "Tippe die grossen Felder an.";
    }
  };

  orbs.forEach((orb) => {
    orb.addEventListener("click", () => {
      orb.classList.toggle("is-live");
      orb.setAttribute("aria-pressed", orb.classList.contains("is-live") ? "true" : "false");
      syncOrbit();
    });
  });

  const showLane = (index) => {
    lanes.forEach((lane, i) => lane.classList.toggle("is-on", i === index));
    panes.forEach((pane) => pane.classList.toggle("is-shown", Number(pane.dataset.pane) === index));
  };

  lanes.forEach((lane) => {
    lane.addEventListener("click", () => showLane(Number(lane.dataset.lane)));
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

  syncOrbit();
})();
