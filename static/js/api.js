/* ── API helpers ──────────────────────────────────────────────────────────── */

async function apiFetch(path) {
  const res = await fetch(path);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `HTTP ${res.status}`);
  }
  return res.json();
}

function fmtDate(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric'
    });
  } catch { return iso; }
}

function subsessionFromPath() {
  // URL is /race/12345678 — extract the last segment
  return parseInt(window.location.pathname.split('/').pop(), 10);
}

function custIdFromPath() {
  return parseInt(window.location.pathname.split('/').pop(), 10);
}
