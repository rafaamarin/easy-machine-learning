import assert from "node:assert/strict";
import test from "node:test";

import { PyodideSession } from "../../assets/js/pyodide_cliente.mjs";

class FakeWorker {
  constructor() {
    this.listeners = new Map();
    this.messages = [];
    this.terminated = false;
  }

  addEventListener(type, listener) {
    this.listeners.set(type, listener);
  }

  postMessage(message) {
    this.messages.push(message);
  }

  terminate() {
    this.terminated = true;
  }

  emit(data) {
    this.listeners.get("message")?.({ data });
  }

  emit_error(message) {
    this.listeners.get("error")?.({ message });
  }
}

test("resolves only the matching run result", async () => {
  const workers = [];
  const session = new PyodideSession({
    worker_factory: () => {
      const worker = new FakeWorker();
      workers.push(worker);
      return worker;
    },
    worker_url: "worker.mjs",
  });
  const pending = session.run("demo", "1 + 1", []);
  const request_id = workers[0].messages[0].request_id;
  workers[0].emit({
    type: "result",
    request_id,
    lab_id: "demo",
    payload: { value: "2" },
  });
  assert.deepEqual(await pending, { value: "2" });

  const second_pending = session.run("otro", "3 + 4", []);
  const second_request_id = workers[0].messages.at(-1).request_id;
  workers[0].emit({
    type: "result",
    request_id: second_request_id,
    lab_id: "otro",
    payload: { value: "7" },
  });
  assert.deepEqual(await second_pending, { value: "7" });
  assert.equal(workers.length, 1);
});

test("cancel terminates worker and rejects active run", async () => {
  const worker = new FakeWorker();
  const session = new PyodideSession({
    worker_factory: () => worker,
    worker_url: "worker.mjs",
  });
  const pending = session.run("infinito", "while True: pass", []);
  session.cancel();
  await assert.rejects(pending, /Ejecución cancelada/);
  assert.equal(worker.terminated, true);
});

test("reports a worker bootstrap failure", async () => {
  const worker = new FakeWorker();
  const session = new PyodideSession({
    worker_factory: () => worker,
    worker_url: "missing-worker.mjs",
  });
  const pending = session.run("demo", "1 + 1", []);
  worker.emit_error("No se encontró pyodide.mjs");
  await assert.rejects(pending, /No se encontró pyodide.mjs/);
});

test("defers worker recreation after failure and ignores late errors from obsolete workers", async () => {
  const workers = [];
  const session = new PyodideSession({
    worker_factory: () => {
      const worker = new FakeWorker();
      workers.push(worker);
      return worker;
    },
    worker_url: "worker.mjs",
  });
  const first_pending = session.run("demo", "1 + 1", []);
  workers[0].emit_error("No se encontró pyodide.mjs");
  await assert.rejects(first_pending, /No se encontró pyodide.mjs/);
  assert.equal(workers.length, 1);

  const second_pending = session.run("demo", "2 + 2", []);
  assert.equal(workers.length, 2);
  workers[0].emit_error("Error tardío del worker obsoleto");
  const request_id = workers[1].messages[0].request_id;
  workers[1].emit({
    type: "result",
    request_id,
    lab_id: "demo",
    payload: { value: "4" },
  });
  assert.deepEqual(await second_pending, { value: "4" });
  assert.equal(workers[0].terminated, true);
});

test("reset sends only the requested lab namespace", () => {
  const worker = new FakeWorker();
  const session = new PyodideSession({
    worker_factory: () => worker,
    worker_url: "worker.mjs",
  });
  session.reset("demo");
  assert.deepEqual(worker.messages.at(-1), { type: "reset", lab_id: "demo" });
  assert.equal(worker.terminated, false);
});

test("forwards streaming stdout and stderr for the active request", async () => {
  const worker = new FakeWorker();
  const events = [];
  const session = new PyodideSession({
    worker_factory: () => worker,
    worker_url: "worker.mjs",
  });
  session.subscribe((message) => events.push(message));
  const pending = session.run("demo", "print('hola')", []);
  const request_id = worker.messages[0].request_id;
  worker.emit({
    type: "stdout",
    request_id,
    lab_id: "demo",
    payload: { value: "hola" },
  });
  worker.emit({
    type: "stderr",
    request_id,
    lab_id: "demo",
    payload: { value: "aviso" },
  });
  worker.emit({
    type: "result",
    request_id,
    lab_id: "demo",
    payload: { value: "" },
  });
  await pending;
  assert.deepEqual(events.map((event) => event.type), ["stdout", "stderr", "result"]);
});

test("rejects concurrent runs until the active request finishes", async () => {
  const worker = new FakeWorker();
  const session = new PyodideSession({
    worker_factory: () => worker,
    worker_url: "worker.mjs",
  });
  const first_pending = session.run("primero", "1", []);
  await assert.rejects(session.run("segundo", "2", []), /Ya hay una ejecución activa/);
  session.cancel();
  await assert.rejects(first_pending, /Ejecución cancelada/);
});

test("recreates its worker after cancellation before accepting another run", async () => {
  const workers = [];
  const session = new PyodideSession({
    worker_factory: () => {
      const worker = new FakeWorker();
      workers.push(worker);
      return worker;
    },
    worker_url: "worker.mjs",
  });
  const cancelled = session.run("demo", "while True: pass", []);
  session.cancel();
  await assert.rejects(cancelled, /Ejecución cancelada/);

  const pending = session.run("demo", "2 + 2", []);
  const request_id = workers[1].messages[0].request_id;
  workers[1].emit({
    type: "result",
    request_id,
    lab_id: "demo",
    payload: { value: "4" },
  });
  assert.deepEqual(await pending, { value: "4" });
  assert.equal(workers.length, 2);
  assert.equal(workers[0].terminated, true);
});
