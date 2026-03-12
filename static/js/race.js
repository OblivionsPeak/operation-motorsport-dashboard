/* ── Race detail page ─────────────────────────────────────────────────────── */

async function init() {
  const subsessionId = subsessionFromPath();
  const wrap  = document.getElementById('race-wrap');
  const meta  = document.getElementById('race-meta');
  const title = document.getElementById('race-title');

  try {
    const data = await apiFetch(`/api/results/${subsessionId}`);

    title.textContent = data.track_name || 'Race Result';

    meta.innerHTML = `
      <div class="race-meta-item">
        <div class="race-meta-label">Track</div>
        <div class="race-meta-value">${data.track_name || '—'}</div>
      </div>
      <div class="race-meta-item">
        <div class="race-meta-label">Date</div>
        <div class="race-meta-value">${fmtDate(data.start_time)}</div>
      </div>
      <div class="race-meta-item">
        <div class="race-meta-label">Drivers</div>
        <div class="race-meta-value">${(data.results || []).length}</div>
      </div>`;

    const results = data.results || [];
    if (!results.length) {
      wrap.innerHTML = '<div class="empty-state"><p>No results available.</p></div>';
      return;
    }

    const rowsHtml = results.map(r => {
      const posClass = r.finish_pos === 1 ? 'pos-1' : r.finish_pos === 2 ? 'pos-2' : r.finish_pos === 3 ? 'pos-3' : '';
      const carNum   = r.car_number ? `<span class="car-num">#${r.car_number}</span>` : '';
      const incClass = r.incidents >= 6 ? 'incident-high' : '';
      const dnf      = r.reason_out && r.reason_out !== 'Running' ? `<span style="color:var(--muted);font-size:0.8rem"> (${r.reason_out})</span>` : '';

      return `<tr>
        <td class="pos-cell ${posClass}">${r.finish_pos}</td>
        <td>${carNum}<a class="driver-link" href="/driver/${r.cust_id}">${r.display_name}</a>${dnf}</td>
        <td>${r.start_pos}</td>
        <td>${r.laps}</td>
        <td>${r.laps_led > 0 ? r.laps_led : '—'}</td>
        <td class="${incClass}">${r.incidents}</td>
        <td style="font-variant-numeric:tabular-nums">${r.best_lap}</td>
      </tr>`;
    }).join('');

    wrap.innerHTML = `
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th class="pos-cell">Pos</th>
              <th>Driver</th>
              <th>Started</th>
              <th>Laps</th>
              <th>Laps Led</th>
              <th>Incidents</th>
              <th>Best Lap</th>
            </tr>
          </thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>`;

  } catch (err) {
    wrap.innerHTML = `<div class="empty-state"><p>Could not load race result: ${err.message}</p></div>`;
  }
}

init();
