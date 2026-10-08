async function getJSON(url, options) {
  const resp = await fetch(url, options);
  let body = null;
  try {
    body = await resp.json();
  } catch {
    // Non-JSON (e.g. the proxy can't reach Flask).
  }
  if (!resp.ok && !(resp.status === 422 && body)) {
    throw new Error(`Server error (${resp.status}). Is the backend running?`);
  }
  return body;
}

export function fetchFuel(region) {
  return getJSON(`/api/fuel?region=${encodeURIComponent(region)}`);
}

export function fetchRegions() {
  return getJSON("/api/regions");
}

export function rankLoads(body) {
  return getJSON("/api/rank", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
