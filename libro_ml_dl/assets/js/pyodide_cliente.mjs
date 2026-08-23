export class PyodideSession {
  constructor({
    worker_factory = (url) => new Worker(url, { type: "module" }),
    worker_url,
  }) {
    this.worker_factory = worker_factory;
    this.worker_url = worker_url;
    this.next_request_id = 1;
    this.listeners = new Set();
    this.pending = null;
    this.create_worker();
  }

  create_worker() {
    const worker = this.worker_factory(this.worker_url);
    this.worker = worker;
    worker.addEventListener("message", (event) => {
      if (worker !== this.worker) return;
      this.handle_message(event.data);
    });
    worker.addEventListener("error", (event) => {
      if (worker !== this.worker) return;
      const message = event.message || "No se pudo iniciar Pyodide";
      const failed_pending = this.pending;
      const lab_id = failed_pending?.lab_id ?? "";
      this.pending = null;
      this.worker = null;
      worker.terminate();
      if (failed_pending) failed_pending.reject(new Error(message));
      for (const listener of this.listeners) {
        listener({
          type: "error",
          request_id: 0,
          lab_id,
          payload: { message, traceback: "" },
        });
      }
    });
    return worker;
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  run(lab_id, code, packages) {
    if (this.pending) {
      return Promise.reject(new Error("Ya hay una ejecución activa"));
    }
    const request_id = this.next_request_id++;
    const worker = this.worker ?? this.create_worker();
    return new Promise((resolve, reject) => {
      this.pending = { request_id, lab_id, resolve, reject };
      worker.postMessage({ type: "run", request_id, lab_id, code, packages });
    });
  }

  handle_message(message) {
    if (!this.pending || message.request_id !== this.pending.request_id) return;
    for (const listener of this.listeners) listener(message);
    if (message.type === "result") {
      this.pending.resolve(message.payload);
      this.pending = null;
    } else if (message.type === "error") {
      this.pending.reject(new Error(message.payload.message));
      this.pending = null;
    }
  }

  cancel() {
    if (this.pending) this.pending.reject(new Error("Ejecución cancelada"));
    this.pending = null;
    const worker = this.worker;
    this.worker = null;
    if (worker) worker.terminate();
    this.create_worker();
  }

  reset(lab_id) {
    if (this.pending) {
      this.cancel();
      return;
    }
    if (this.worker) this.worker.postMessage({ type: "reset", lab_id });
  }
}
