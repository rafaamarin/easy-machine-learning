import { loadPyodide } from "../vendor/pyodide/pyodide.mjs";
import { execute_python_run } from "./pyodide_execution.mjs";

const index_url = new URL("../vendor/pyodide/", import.meta.url).href;
let runtime_promise;
const loaded_packages = new Set();
const namespaces = new Map();

function get_runtime(request_id, lab_id) {
  if (!runtime_promise) {
    runtime_promise = loadPyodide({ indexURL: index_url }).catch((error) => {
      runtime_promise = undefined;
      throw error;
    });
  }
  self.postMessage({
    type: "ready",
    request_id,
    lab_id,
    payload: { stage: "loading" },
  });
  return runtime_promise;
}

function get_namespace(runtime, lab_id) {
  if (!namespaces.has(lab_id)) {
    const dict_constructor = runtime.globals.get("dict");
    const namespace = dict_constructor();
    dict_constructor.destroy();
    namespaces.set(lab_id, namespace);
  }
  return namespaces.get(lab_id);
}

self.addEventListener("message", async (event) => {
  if (event.data?.type === "reset") {
    const namespace = namespaces.get(event.data.lab_id);
    if (namespace && typeof namespace.destroy === "function") namespace.destroy();
    namespaces.delete(event.data.lab_id);
    return;
  }
  if (event.data?.type !== "run") return;
  const { request_id, lab_id, code, packages } = event.data;
  try {
    const runtime = await get_runtime(request_id, lab_id);
    runtime.setStdout({
      batched: (value) => self.postMessage({
        type: "stdout",
        request_id,
        lab_id,
        payload: { value },
      }),
    });
    runtime.setStderr({
      batched: (value) => self.postMessage({
        type: "stderr",
        request_id,
        lab_id,
        payload: { value },
      }),
    });
    const missing_packages = packages.filter((name) => !loaded_packages.has(name));
    if (missing_packages.length) {
      await runtime.loadPackage(missing_packages);
      for (const package_name of missing_packages) loaded_packages.add(package_name);
    }
    if (packages.includes("matplotlib")) {
      await runtime.runPythonAsync(
        "import matplotlib; matplotlib.use('Agg', force=True)",
      );
    }
    const namespace = get_namespace(runtime, lab_id);
    await execute_python_run({
      runtime,
      request_id,
      lab_id,
      code,
      namespace,
      post_message: (message) => self.postMessage(message),
    });
  } catch (error) {
    self.postMessage({
      type: "error",
      request_id,
      lab_id,
      payload: {
        message: error instanceof Error ? error.message : String(error),
        traceback: error instanceof Error ? error.stack ?? "" : "",
      },
    });
  }
});
