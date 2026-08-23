import assert from "node:assert/strict";
import test from "node:test";

import { create_progress_store } from "../../assets/js/progreso.mjs";

function fake_storage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  };
}

test("persists completed checkpoints and last location", () => {
  const storage = fake_storage();
  const store = create_progress_store(storage);
  store.set_complete("00_inicio:como_usar", true);
  store.set_last_location("/index.html#como_usar");

  const restored = create_progress_store(storage).get_state();
  assert.equal(restored.completed["00_inicio:como_usar"], true);
  assert.equal(restored.last_location, "/index.html#como_usar");
});

test("recovers from corrupt storage", () => {
  const storage = fake_storage();
  storage.setItem("libro_ml_dl_progress_v1", "not-json");
  assert.deepEqual(create_progress_store(storage).get_state(), {
    schema_version: 1,
    completed: {},
    last_location: null,
  });
});

test("recovers from a structurally invalid completed map", () => {
  const storage = fake_storage();
  storage.setItem(
    "libro_ml_dl_progress_v1",
    JSON.stringify({ schema_version: 1, completed: null, last_location: null }),
  );
  assert.deepEqual(create_progress_store(storage).get_state(), {
    schema_version: 1,
    completed: {},
    last_location: null,
  });
});
