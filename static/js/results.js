/* ── Results list page ────────────────────────────────────────────────────── */

async function init() {
  const wrap = document.getElementById('results-wrap');
  try {
    const data    = await apiFetch('/api/results');
    const results = data.results || [];

    if (!results.length) {
      wrap.innerHTML = '<div class="empty-state"><p>No completed races yet.</p></div>';
      return;
    }

    const html = results.map((r, i) => {
      const num   = results.length - i;
      const date  = fmtDate(r.start_time);
      return `
        <a class="race-card" href="/race/${r.subsession_id}">
          <div class="race-card-left">
            <span class="race-num">${String(num).padStart(2, '0')}</span>
            <div>
              <div class="race-info-track">${r.track_name || 'Unknown Track'}</div>
              <div class="race-info-date">${date}</div>
            </div>
          </div>
          <div class="race-card-right">${r.session_name || ''}</div>
          <div class="race-card-arrow">›</div>
        </a>`;
    }).join('');

    wrap.innerHTML = `<div class="race-list">${html}</div>`;
  } catch (err) {
    wrap.innerHTML = `<div class="empty-state"><p>Could not load results: ${err.message}</p></div>`;
  }
}

init();
