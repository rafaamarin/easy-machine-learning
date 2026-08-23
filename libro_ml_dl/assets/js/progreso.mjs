const storage_key = "libro_ml_dl_progress_v1";

const empty_state = () => ({
  schema_version: 1,
  completed: {},
  last_location: null,
});

export function create_progress_store(storage) {
  function get_state() {
    const raw = storage.getItem(storage_key);
    if (!raw) return empty_state();

    try {
      const parsed = JSON.parse(raw);
      const completed_is_record =
        parsed.completed !== null &&
        typeof parsed.completed === "object" &&
        !Array.isArray(parsed.completed);

      if (parsed.schema_version !== 1 || !completed_is_record) {
        return empty_state();
      }

      return {
        schema_version: 1,
        completed: parsed.completed,
        last_location:
          typeof parsed.last_location === "string" ? parsed.last_location : null,
      };
    } catch {
      return empty_state();
    }
  }

  function save(state) {
    storage.setItem(storage_key, JSON.stringify(state));
  }

  return {
    get_state,
    set_complete(checkpoint_id, complete) {
      const state = get_state();
      state.completed[checkpoint_id] = Boolean(complete);
      save(state);
    },
    set_last_location(location) {
      const state = get_state();
      state.last_location = location;
      save(state);
    },
    reset() {
      storage.removeItem(storage_key);
    },
  };
}
