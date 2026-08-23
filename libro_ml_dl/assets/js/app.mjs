import { create_progress_store } from "./progreso.mjs";
import { validate_jupyter_url } from "./jupyter_url.mjs";
import { mount_labs } from "./laboratorios.mjs";

const theme_key = "libro_ml_dl_theme_v1";
const root = document.documentElement;
const theme_button = document.querySelector("[data-theme-toggle]");
const saved_theme = localStorage.getItem(theme_key);

if (saved_theme === "dark" || saved_theme === "light") {
  root.dataset.theme = saved_theme;
}

theme_button?.addEventListener("click", () => {
  const next_theme = root.dataset.theme === "dark" ? "light" : "dark";
  root.dataset.theme = next_theme;
  localStorage.setItem(theme_key, next_theme);
});

const query = new URLSearchParams(window.location.search);
const jupyter_url = query.get("jupyter_url");
if (jupyter_url) {
  const valid_jupyter_url = validate_jupyter_url(jupyter_url);
  if (valid_jupyter_url) {
    sessionStorage.setItem("libro_ml_dl_jupyter_url", valid_jupyter_url);
  } else {
    sessionStorage.removeItem("libro_ml_dl_jupyter_url");
  }
  history.replaceState({}, "", window.location.pathname + window.location.hash);
}

const current_jupyter_url = sessionStorage.getItem("libro_ml_dl_jupyter_url");
const jupyter_link = document.querySelector("[data-jupyter-link]");
const valid_jupyter_url = validate_jupyter_url(current_jupyter_url);
if (!valid_jupyter_url) {
  sessionStorage.removeItem("libro_ml_dl_jupyter_url");
}
if (valid_jupyter_url && jupyter_link instanceof HTMLAnchorElement) {
  jupyter_link.href = valid_jupyter_url;
  jupyter_link.hidden = false;
}

const progress_store = create_progress_store(localStorage);
const checkpoints = [...document.querySelectorAll("input[data-progress-id]")];
const progress_meter = document.querySelector("[data-progress-meter]");
const progress_text = document.querySelector("[data-progress-text]");

function nearest_section_hash(checkpoint) {
  let hash = window.location.hash;
  const headings = document.querySelectorAll("main h2[id], main h3[id]");

  for (const heading of headings) {
    const position = heading.compareDocumentPosition(checkpoint);
    if (position & Node.DOCUMENT_POSITION_FOLLOWING) {
      hash = `#${heading.id}`;
    } else {
      break;
    }
  }

  return hash;
}

function render_progress() {
  const state = progress_store.get_state();
  let completed_count = 0;

  for (const checkpoint of checkpoints) {
    const complete = state.completed[checkpoint.dataset.progressId] === true;
    checkpoint.checked = complete;
    if (complete) completed_count += 1;
  }

  if (progress_meter instanceof HTMLProgressElement) {
    progress_meter.max = Math.max(checkpoints.length, 1);
    progress_meter.value = completed_count;
    progress_meter.setAttribute(
      "aria-label",
      `Progreso: ${completed_count} de ${checkpoints.length}`,
    );
  }

  if (progress_text instanceof HTMLOutputElement) {
    progress_text.textContent = `${completed_count} de ${checkpoints.length}`;
  }

  const resume_link = document.querySelector("[data-resume-link]");
  if (state.last_location && resume_link instanceof HTMLAnchorElement) {
    resume_link.href = state.last_location;
    resume_link.textContent = "Retomar donde lo dejaste";
    resume_link.hidden = false;
  }
}

for (const checkpoint of checkpoints) {
  checkpoint.addEventListener("change", () => {
    progress_store.set_complete(checkpoint.dataset.progressId, checkpoint.checked);
    const hash = nearest_section_hash(checkpoint);
    progress_store.set_last_location(`${window.location.pathname}${hash}`);
    render_progress();
  });
}

render_progress();
mount_labs();
