/* ── Standings page ───────────────────────────────────────────────────────── */

let allRows    = [];
let sortKey    = 'position';
let sortAsc    = true;
let currentSeason = null;

async function init() {
  // Load seasons for the dropdown
  try {
    const { seasons } = await apiFetch('/api/seasons');
    buildSeasonSelect(seasons);
  } catch (_) {}

  await loadStandings();
}

async function loadStandings(seasonId) {
  const wrap = document.getElementById('standings-wrap');
  wrap.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading standings…</p></div>';

  try {
    const url  = seasonId ? `/api/standings?season_id=${seasonId}` : '/api/standings';
    const data = await apiFetch(url);

    currentSeason = data.season_id;
    allRows = data.standings || [];

    updateSubtitle();
    renderTable();

    document.getElementById('refresh-btn').style.display = 'inline-flex';
  } catch (err) {
    wrap.innerHTML = `<div class="empty-state"><p>Could not load standings: ${err.message}</p></div>`;
  }
}

function buildSeasonSelect(seasons) {
  const sel = document.getElementById('season-select');
  if (!seasons.length) return;
  sel.style.display = 'block';
  seasons.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s.season_id;
    opt.textContent = s.season_name;
    if (s.active) opt.selected = true;
    sel.appendChild(opt);
  });
  sel.addEventListener('change', () => loadStandings(parseInt(sel.value)));
}

function updateSubtitle() {
  const sub = document.getElementById('season-subtitle');
  if (sub) sub.textContent = `${allRows.length} drivers · Season ${currentSeason}`;
}

function renderTable() {
  const wrap = document.getElementById('standings-wrap');
  if (!allRows.length) {
    wrap.innerHTML = '<div class="empty-state"><p>No standings data yet — check back after the first race.</p></div>';
    return;
  }

  const sorted = [...allRows].sort((a, b) => {
    let av = a[sortKey] ?? 0, bv = b[sortKey] ?? 0;
    if (typeof av === 'string') av = av.toLowerCase();
    if (typeof bv === 'string') bv = bv.toLowerCase();
    if (av < bv) return sortAsc ? -1 : 1;
    if (av > bv) return sortAsc ? 1 : -1;
    return 0;
  });

  const cols = [
    { key: 'position',   label: 'Pos',        cls: 'pos-cell' },
    { key: 'display_name', label: 'Driver',   cls: '' },
    { key: 'starts',     label: 'Starts',     cls: '' },
    { key: 'wins',       label: 'Wins',       cls: '' },
    { key: 'top5',       label: 'Top 5',      cls: '' },
    { key: 'laps_led',   label: 'Laps Led',   cls: '' },
    { key: 'incidents',  label: 'Incidents',  cls: '' },
    { key: 'avg_finish', label: 'Avg Finish', cls: '' },
    { key: 'avg_start',  label: 'Avg Start',  cls: '' },
  ];

  const headerHtml = cols.map(c => {
    const sorted = c.key === sortKey ? 'sorted' : '';
    const arrow  = c.key === sortKey ? (sortAsc ? ' ↑' : ' ↓') : '';
    return `<th class="${sorted}" data-key="${c.key}">${c.label}${arrow}</th>`;
  }).join('');

  const rowsHtml = sorted.map(r => {
    const posClass  = r.position === 1 ? 'pos-1' : r.position === 2 ? 'pos-2' : r.position === 3 ? 'pos-3' : '';
    const carNum    = r.car_number ? `<span class="car-num">#${r.car_number}</span>` : '';
    const winDisp   = r.wins > 0 ? `<span class="win-count">${r.wins}</span>` : r.wins;
    const incClass  = r.incidents >= 10 ? 'incident-high' : '';

    return `<tr>
      <td class="pos-cell ${posClass}">${r.position}</td>
      <td>${carNum}<a class="driver-link" href="/driver/${r.cust_id}">${r.display_name}</a></td>
      <td>${r.starts}</td>
      <td>${winDisp}</td>
      <td>${r.top5}</td>
      <td>${r.laps_led}</td>
      <td class="${incClass}">${r.incidents}</td>
      <td>${r.avg_finish}</td>
      <td>${r.avg_start}</td>
    </tr>`;
  }).join('');

  wrap.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead><tr>${headerHtml}</tr></thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    </div>`;

  // Sort on header click
  wrap.querySelectorAll('thead th').forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.key;
      if (sortKey === key) sortAsc = !sortAsc;
      else { sortKey = key; sortAsc = key === 'position'; }
      renderTable();
    });
  });
}

// Refresh button
document.getElementById('refresh-btn')?.addEventListener('click', () => {
  loadStandings(currentSeason);
});

init();
