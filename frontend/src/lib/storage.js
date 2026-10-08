// Versioned localStorage. Every read/write is wrapped: private mode or a full
// disk can throw, and the app must still work (it just won't remember).

const KEYS = {
  settings: "haulmath.settings.v1",
  trip: "haulmath.trip.v1",
  loads: "haulmath.loads.v1",
};

export function load(name, fallback) {
  try {
    const raw = localStorage.getItem(KEYS[name]);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function save(name, value) {
  try {
    localStorage.setItem(KEYS[name], JSON.stringify(value));
  } catch {
    // Not fatal: the app keeps working for this visit.
  }
}
