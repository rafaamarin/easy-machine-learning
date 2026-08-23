import assert from "node:assert/strict";
import test from "node:test";

import { validate_jupyter_url } from "../../assets/js/jupyter_url.mjs";

test("accepts only explicit loopback HTTP Jupyter URLs", () => {
  assert.equal(
    validate_jupyter_url("http://127.0.0.1:8888/lab?token=temporal"),
    "http://127.0.0.1:8888/lab?token=temporal",
  );
});

test("rejects unsafe or ambiguous Jupyter URLs", () => {
  for (const value of [
    "https://127.0.0.1:8888/lab",
    "http://localhost:8888/lab",
    "http://127.0.0.1/lab",
    "http://user@127.0.0.1:8888/lab",
    "http://127.0.0.1:8888@evil.example/lab",
  ]) {
    assert.equal(validate_jupyter_url(value), null, value);
  }
});
