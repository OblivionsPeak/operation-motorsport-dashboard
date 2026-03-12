/* ── Driver profile page ──────────────────────────────────────────────────── */

async function init() {
  const custId = custIdFromPath();
  const wrap   = document.getElementById('driver-wrap');

  try {
    const data   = await apiFetch(`/api/drivers/${custId}`);
    const driver = data.driver  || {};
    const stats  = data.stats   || {};
    const results = data.results || [];

    const statsHtml = [
      { label: 'Starts',     value: stats.starts    || 0 },
      { label: 'Wins',       value: stats.wins      || 0 },
      { label: 'Top 5',      value: stats.top5      || 0 },
      { label: 'Incidents',  value: stats.incidents || 0 },
      { label: 'Avg Finish', value: stats.avg_finish || '—' },
    ].map(s => `
      <div class="stat-card">
        <div class="stat-value">${s.value}</div>
        <div class="stat-label">${s.label}</div>
      </div>`).join('');

    const resultsHtml = results.length ? results.map(r => {
      const posClass = r.finish_pos === 1 ? 'pos-1' : r.finish_pos === 2 ? 'pos-2' : r.finish_pos === 3 ? 'pos-3' : '';
      const incClass = r.incidents >= 6 ? 'incident-high' : '';
      return `<tr>
        <td class="pos-cell ${posClass}">${r.finish_pos}</td>
        <td><a class="driver-link" href="/race/${r.subsession_id}">${r.track_name || '—'}</a></td>
        <td>${fmtDate(r.start_time)}</td>
        <td>${r.start_pos}</td>
        <td>${r.laps}</td>
        <td>${r.laps_led > 0 ? r.laps_led : '—'}</td>
        <td class="${incClass}">${r.incidents}</td>
        <td style="font-variant-numeric:tabular-nums">${r.best_lap}</td>
      </tr>`;
    }).join('') : '<tr><td colspan="8" style="text-align:center;padding:32px;color:var(--muted)">No race results yet.</td></tr>';

    wrap.innerHTML = `
      <div class="driver-header">
        <div>
          <h1 class="driver-name">${driver.display_name || 'Driver'}</h1>
          ${driver.club_name ? `<p class="driver-club">${driver.club_name}</p>` : ''}
        </div>
      </div>

      <div class="stat-grid">${statsHtml}</div>

      <h2 class="section-title" style="margin-bottom:16px">Race History</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th class="pos-cell">Pos</th>
              <th>Track</th>
              <th>Date</th>
              <th>Started</th>
              <th>Laps</th>
              <th>Laps Led</th>
              <th>Incidents</th>
              <th>Best Lap</th>
            </tr>
          </thead>
          <tbody>${resultsHtml}</tbody>
        </table>
      </div>`;

  } catch (err) {
    wrap.innerHTML = `<div class="empty-state"><p>Could not load driver: ${err.message}</p></div>`;
  }
}

init();
