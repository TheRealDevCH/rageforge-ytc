(() => {
  const orbs = Array.from(document.querySelectorAll(".orb"));
  const echo = document.getElementById("orbitEcho");
  const lanes = Array.from(document.querySelectorAll(".lane"));
  const panes = Array.from(document.querySelectorAll(".lens-pane"));

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

  syncOrbit();
})();
