import assert from "node:assert/strict";
import test from "node:test";

import { execute_python_run } from "../../assets/js/pyodide_execution.mjs";

test("closes figures before and after a failed Python execution", async () => {
  const calls = [];
  const runtime = {
    async runPythonAsync(code) {
      calls.push(code);
      if (code.includes("plt.close")) return undefined;
      throw new Error("falló el laboratorio");
    },
  };

  await assert.rejects(
    execute_python_run({
      runtime,
      request_id: 1,
      lab_id: "demo",
      code: "raise ValueError('falló')",
      namespace: {},
      post_message: () => {},
    }),
    /falló el laboratorio/,
  );
  assert.equal(calls.filter((code) => code.includes("plt.close")).length, 2);
});

test("destroys the result when figure delivery fails", async () => {
  const result = { destroyed: false, destroy() { this.destroyed = true; } };
  const runtime = {
    async runPythonAsync(code) {
      if (code.includes("json.dumps")) return '["data:image/png;base64,a"]';
      if (code.includes("plt.close")) return undefined;
      return result;
    },
  };

  await assert.rejects(
    execute_python_run({
      runtime,
      request_id: 1,
      lab_id: "demo",
      code: "resultado",
      namespace: {},
      post_message: (message) => {
        if (message.type === "figure") throw new Error("falló postMessage");
      },
    }),
    /falló postMessage/,
  );
  assert.equal(result.destroyed, true);
});
