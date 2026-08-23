import { PyodideSession } from "./pyodide_cliente.mjs";

export function mount_labs(root = document) {
  const labs = [...root.querySelectorAll("[data-python-lab]")];
  if (!labs.length) return;
  const worker_url = new URL("./pyodide_worker.mjs", import.meta.url);
  const session = new PyodideSession({ worker_url });
  for (const lab of labs) {
    mount_lab(lab, session, labs);
  }
}

function set_busy(labs, active_lab) {
  for (const lab of labs) {
    lab.querySelector("[data-run]").disabled = active_lab !== null;
    lab.querySelector("[data-cancel]").disabled = lab !== active_lab;
    lab.querySelector("[data-reset]").disabled = active_lab !== null;
  }
}

function mount_lab(lab, session, labs) {
  const code = lab.querySelector("[data-lab-code]");
  const output = lab.querySelector("[data-lab-output]");
  const figures = lab.querySelector("[data-lab-figures]");
  const status = lab.querySelector("[data-lab-status]");
  const run_button = lab.querySelector("[data-run]");
  const cancel_button = lab.querySelector("[data-cancel]");
  const reset_button = lab.querySelector("[data-reset]");
  const lab_id = lab.dataset.pythonLab;
  const original_code = code.value;
  const packages = (lab.dataset.packages ?? "").split(",").filter(Boolean);

  session.subscribe((message) => {
    if (message.lab_id !== lab_id) return;
    if (message.type === "stdout" || message.type === "stderr") {
      output.textContent += `${message.payload.value}\n`;
    }
    if (message.type === "figure") {
      const image = document.createElement("img");
      image.src = message.payload.src;
      image.alt = `Resultado visual del laboratorio ${lab.dataset.pythonLab}`;
      figures.append(image);
    }
    if (message.type === "error") {
      output.textContent += message.payload.traceback || message.payload.message;
      const fallback = document.querySelector(
        `[data-static-output-for="${CSS.escape(lab.dataset.pythonLab)}"]`,
      );
      if (fallback instanceof HTMLDetailsElement) fallback.open = true;
    }
  });

  run_button.addEventListener("click", async () => {
    output.textContent = "";
    figures.replaceChildren();
    status.textContent = "Ejecutando";
    set_busy(labs, lab);
    try {
      const result = await session.run(lab_id, code.value, packages);
      if (result.value) output.textContent += result.value;
      status.textContent = "Completado";
    } catch (error) {
      status.textContent = error.message === "Ejecución cancelada" ? "Cancelado" : "Error";
      if (!output.textContent.includes(error.message)) output.textContent += error.message;
    } finally {
      set_busy(labs, null);
    }
  });
  cancel_button.addEventListener("click", () => session.cancel());
  reset_button.addEventListener("click", () => {
    session.reset(lab_id);
    code.value = original_code;
    output.textContent = "";
    figures.replaceChildren();
    status.textContent = "Sin ejecutar";
  });
}
