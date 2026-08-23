function destroy_pyproxy(value) {
  if (value && typeof value.destroy === "function") value.destroy();
}

async function close_figures(runtime) {
  let result;
  try {
    result = await runtime.runPythonAsync(`
try:
    import matplotlib.pyplot as plt
    plt.close("all")
except ImportError:
    pass
`);
  } finally {
    destroy_pyproxy(result);
  }
}

async function collect_figures(runtime) {
  let result;
  try {
    result = await runtime.runPythonAsync(`
import base64
import io
import json

_book_figures = []
try:
    import matplotlib.pyplot as plt
    for _number in plt.get_fignums():
        _buffer = io.BytesIO()
        plt.figure(_number).savefig(_buffer, format="png", bbox_inches="tight")
        _encoded = base64.b64encode(_buffer.getvalue()).decode("ascii")
        _book_figures.append("data:image/png;base64," + _encoded)
    plt.close("all")
except ImportError:
    pass
json.dumps(_book_figures)
`);
    return JSON.parse(String(result));
  } finally {
    destroy_pyproxy(result);
  }
}

export async function execute_python_run({
  runtime,
  request_id,
  lab_id,
  code,
  namespace,
  post_message,
}) {
  await close_figures(runtime);
  let result;
  try {
    result = await runtime.runPythonAsync(code, { globals: namespace });
    for (const figure of await collect_figures(runtime)) {
      post_message({
        type: "figure",
        request_id,
        lab_id,
        payload: { src: figure },
      });
    }
    post_message({
      type: "result",
      request_id,
      lab_id,
      payload: { value: result === undefined ? "" : String(result) },
    });
  } finally {
    destroy_pyproxy(result);
    await close_figures(runtime);
  }
}
