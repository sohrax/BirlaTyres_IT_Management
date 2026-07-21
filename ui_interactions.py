import streamlit as st
import streamlit.components.v1 as components


def render_cursor_interactions() -> None:
    components.html(
        """
        <script>
        (() => {
          const doc = window.parent.document;
          if (doc.documentElement.dataset.premiumCursorReady === "true") return;
          doc.documentElement.dataset.premiumCursorReady = "true";

          const particleAngles = [-62, -28, 12, 44, 78];
          const interactiveCards = [
            ".hero-panel",
            ".kpi-card",
            ".enterprise-grid-card",
            ".enterprise-empty-state",
            "[data-testid='stPlotlyChart']",
            "form[data-testid='stForm']",
            ".sidebar-panel"
          ].join(",");

          const createPulse = (x, y) => {
            const pulse = doc.createElement("span");
            pulse.className = "cursor-energy-pulse";
            pulse.style.left = `${x}px`;
            pulse.style.top = `${y}px`;
            doc.body.appendChild(pulse);
            pulse.addEventListener("animationend", () => pulse.remove(), { once: true });

            particleAngles.forEach((angle, index) => {
              const particle = doc.createElement("span");
              particle.className = "cursor-energy-particle";
              particle.style.left = `${x}px`;
              particle.style.top = `${y}px`;
              particle.style.setProperty("--particle-angle", `${angle}deg`);
              particle.style.setProperty("--particle-distance", `${7 + (index % 2) * 4}px`);
              doc.body.appendChild(particle);
              particle.addEventListener("animationend", () => particle.remove(), { once: true });
            });
          };

          const createButtonRipple = (event) => {
            const button = event.target.closest("button, [role='button'], a");
            if (!button) return;
            button.classList.add("premium-clicked");
            window.setTimeout(() => button.classList.remove("premium-clicked"), 220);

            const rect = button.getBoundingClientRect();
            const ripple = doc.createElement("span");
            ripple.className = "premium-button-ripple";
            ripple.style.left = `${event.clientX - rect.left}px`;
            ripple.style.top = `${event.clientY - rect.top}px`;
            button.appendChild(ripple);
            ripple.addEventListener("animationend", () => ripple.remove(), { once: true });

            if (button.closest("[data-testid='stSidebar']")) {
              button.classList.add("sidebar-click-light");
              window.setTimeout(() => button.classList.remove("sidebar-click-light"), 260);
            }
          };

          doc.addEventListener("click", (event) => {
            createPulse(event.clientX, event.clientY);
            createButtonRipple(event);
          }, { passive: true });

          doc.addEventListener("pointermove", (event) => {
            const card = event.target.closest(interactiveCards);
            if (!card) return;
            const rect = card.getBoundingClientRect();
            const xPercent = ((event.clientX - rect.left) / rect.width) * 100;
            const yPercent = ((event.clientY - rect.top) / rect.height) * 100;
            const tiltX = ((event.clientX - rect.left) / rect.width - 0.5) * 3.2;
            const tiltY = (((event.clientY - rect.top) / rect.height - 0.5) * -3.2);
            card.classList.add("premium-card-interactive");
            card.style.setProperty("--cursor-x", `${xPercent}%`);
            card.style.setProperty("--cursor-y", `${yPercent}%`);
            card.style.setProperty("--tilt-x", `${tiltX}deg`);
            card.style.setProperty("--tilt-y", `${tiltY}deg`);
          }, { passive: true });

          doc.addEventListener("pointerout", (event) => {
            const card = event.target.closest(interactiveCards);
            if (!card || card.contains(event.relatedTarget)) return;
            card.classList.remove("premium-card-interactive");
            card.style.removeProperty("--tilt-x");
            card.style.removeProperty("--tilt-y");
          }, { passive: true });
        })();
        </script>
        """,
        height=0,
        width=0,
    )
