/**
 * AstroHistory v6 — Linha da Vida (canvas) e filtros do módulo pessoal.
 * Lê o JSON compacto em <script id="natal-data"> e desenha episódios/janelas por planeta em trânsito.
 * Sem dependências externas.
 */
(function () {
  var el = document.getElementById('natal-data');
  if (!el) return;
  var D = JSON.parse(el.textContent);
  var canvas = document.getElementById('life-timeline');
  var tooltip = document.getElementById('life-tooltip');
  if (!canvas) return;

  var LANES = ['pluto', 'neptune', 'uranus', 'saturn', 'chiron', 'mean_node', 'jupiter', 'mars', 'moon'];
  var LANE_LABEL = { pluto: '♇', neptune: '♆', uranus: '♅', saturn: '♄', chiron: '⚷', mean_node: '☊', jupiter: '♃', mars: '♂', moon: '☽' };
  var TONE_COLOR = { challenging: '#f43f5e', flowing: '#10b981', focus: '#fbbf24' };
  var FAMILY_TONE = { challenging: 'challenging', flowing: 'flowing', focus: 'focus' };
  var lanes = LANES.filter(function (b) { return D.bodies.indexOf(b) >= 0; });
  var y0 = D.axis.year_start, y1 = D.axis.year_end + 1;
  var view = { from: y0, to: y1 };
  var filters = { bodies: {}, tones: { challenging: true, flowing: true, focus: true }, minW: 0 };
  lanes.forEach(function (b) { filters.bodies[b] = true; });

  function dateToYear(s) {
    var y = parseInt(s.slice(0, 4), 10), m = parseInt(s.slice(5, 7), 10), d = parseInt(s.slice(8, 10), 10);
    return y + (m - 1) / 12 + (d - 1) / 365.25;
  }
  var episodes = D.episodes.map(function (e) {
    return { id: e.i, body: e.b, point: e.p, aspect: e.a, tone: FAMILY_TONE[e.f] || 'focus', s: dateToYear(e.s), e: dateToYear(e.e) + 1 / 365.25,
      start: e.s, end: e.e, hits: e.h.map(dateToYear), hitsRaw: e.h, retro: e.r, name: e.n, w: e.w, nw: e.nw, label: e.bs + ' ' + e.as + ' ' + e.ps };
  });
  var cycleByEpisode = {};
  D.episodes.forEach(function (e) { if (e.c) cycleByEpisode[e.i] = e.c; });
  // Mapa de calor: navegação por clique sem URL por célula
  var hm = document.getElementById('heatmap');
  if (hm) hm.addEventListener('click', function (evt) {
    var cell = evt.target.closest('[data-y]'); if (!cell) return;
    var url = new URL(window.location.href); url.searchParams.set('focus_year', cell.getAttribute('data-y')); url.hash = 'ano-foco';
    window.location.href = url.toString();
  });

  var ctx = canvas.getContext('2d');
  var hitboxes = [];

  function layout() {
    var cssW = canvas.clientWidth || canvas.parentElement.clientWidth || 900;
    var laneH = 30, top = 28, bottom = 26, left = 34, right = 10;
    var cssH = top + lanes.length * laneH + bottom;
    var dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(cssW * dpr); canvas.height = Math.round(cssH * dpr);
    canvas.style.height = cssH + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { w: cssW, h: cssH, laneH: laneH, top: top, left: left, right: right };
  }

  function xOf(year, L) { return L.left + (year - view.from) / (view.to - view.from) * (L.w - L.left - L.right); }

  function draw() {
    var L = layout();
    hitboxes = [];
    ctx.clearRect(0, 0, L.w, L.h);
    var isLight = document.documentElement.classList.contains('theme-light');
    var grid = isLight ? 'rgba(15,23,42,0.12)' : 'rgba(148,163,184,0.18)';
    var text = isLight ? '#334155' : '#94a3b8';
    // eixos de anos
    var span = view.to - view.from;
    var step = span > 60 ? 10 : span > 25 ? 5 : span > 8 ? 2 : 1;
    ctx.font = '10px JetBrains Mono, monospace'; ctx.fillStyle = text; ctx.textAlign = 'center';
    for (var y = Math.ceil(view.from / step) * step; y <= view.to; y += step) {
      var x = xOf(y, L);
      ctx.strokeStyle = grid; ctx.beginPath(); ctx.moveTo(x, L.top - 6); ctx.lineTo(x, L.h - 22); ctx.stroke();
      ctx.fillText(String(y), x, L.h - 8);
      var age = y - y0;
      if (step >= 5) { ctx.fillStyle = isLight ? '#64748b' : '#64748b'; ctx.fillText(age + 'a', x, L.top - 12); ctx.fillStyle = text; }
    }
    // faixas
    lanes.forEach(function (b, i) {
      var yTop = L.top + i * L.laneH;
      ctx.fillStyle = i % 2 ? 'rgba(148,163,184,0.04)' : 'rgba(148,163,184,0.08)';
      ctx.fillRect(L.left, yTop, L.w - L.left - L.right, L.laneH);
      ctx.fillStyle = filters.bodies[b] ? '#fbbf24' : '#475569'; ctx.font = '15px serif'; ctx.textAlign = 'center';
      ctx.fillText(LANE_LABEL[b] || b, L.left / 2, yTop + L.laneH / 2 + 5);
    });
    // hoje
    var tx = xOf(dateToYear(D.today), L);
    if (tx >= L.left && tx <= L.w - L.right) {
      ctx.strokeStyle = '#38bdf8'; ctx.setLineDash([4, 3]); ctx.beginPath(); ctx.moveTo(tx, L.top - 4); ctx.lineTo(tx, L.h - 22); ctx.stroke(); ctx.setLineDash([]);
    }
    // episódios
    episodes.forEach(function (ep) {
      if (!filters.bodies[ep.body] || !filters.tones[ep.tone] || ep.w < filters.minW) return;
      if (ep.e < view.from || ep.s > view.to) return;
      var li = lanes.indexOf(ep.body); if (li < 0) return;
      var yTop = L.top + li * L.laneH + 5, h = L.laneH - 10;
      var xa = Math.max(L.left, xOf(ep.s, L)), xb = Math.min(L.w - L.right, xOf(ep.e, L));
      var wpx = Math.max(2, xb - xa);
      var col = TONE_COLOR[ep.tone];
      ctx.globalAlpha = 0.35 + 0.55 * Math.min(1, ep.w);
      ctx.fillStyle = col; ctx.fillRect(xa, yTop, wpx, h);
      ctx.globalAlpha = 1;
      ep.hits.forEach(function (hy, k) {
        var hx = xOf(hy, L); if (hx < L.left || hx > L.w - L.right) return;
        ctx.beginPath(); ctx.arc(hx, yTop + h / 2, 2.6, 0, Math.PI * 2);
        if (ep.retro[k]) { ctx.strokeStyle = '#f8fafc'; ctx.lineWidth = 1.2; ctx.stroke(); } else { ctx.fillStyle = '#f8fafc'; ctx.fill(); }
      });
      hitboxes.push({ x: xa, y: yTop, w: wpx, h: h, ep: ep });
    });
  }

  function showTip(evt, box) {
    if (!tooltip) return;
    var ep = box.ep;
    var cyc = cycleByEpisode[ep.id];
    var hits = ep.hitsRaw.map(function (d, k) { return d + (ep.retro[k] ? ' ℞' : ''); }).join(', ');
    tooltip.innerHTML = '<div class="font-semibold text-slate-100">' + ep.label + ' · ' + ep.name + (cyc ? ' <span class="text-amber-300">· ' + cyc + '</span>' : '') + '</div>' +
      '<div class="font-mono text-[11px] text-slate-300">' + ep.start + ' → ' + ep.end + ' · ' + (D.lang === 'en' ? 'passes' : 'passagens') + ': ' + ep.hitsRaw.length + '</div>' +
      (hits ? '<div class="font-mono text-[11px] text-slate-400">' + hits + '</div>' : '');
    tooltip.hidden = false;
    var r = canvas.getBoundingClientRect();
    var left = evt.clientX - r.left + 12, top = evt.clientY - r.top + 12;
    if (left + 320 > r.width) left = Math.max(0, r.width - 320);
    tooltip.style.left = left + 'px'; tooltip.style.top = top + 'px';
  }
  canvas.addEventListener('mousemove', function (evt) {
    var r = canvas.getBoundingClientRect(); var mx = evt.clientX - r.left, my = evt.clientY - r.top;
    for (var i = hitboxes.length - 1; i >= 0; i--) {
      var b = hitboxes[i];
      if (mx >= b.x && mx <= b.x + b.w && my >= b.y && my <= b.y + b.h) { showTip(evt, b); canvas.style.cursor = 'pointer'; return; }
    }
    if (tooltip) tooltip.hidden = true; canvas.style.cursor = 'default';
  });
  canvas.addEventListener('mouseleave', function () { if (tooltip) tooltip.hidden = true; });
  canvas.addEventListener('click', function (evt) {
    var r = canvas.getBoundingClientRect(); var mx = evt.clientX - r.left, my = evt.clientY - r.top;
    for (var i = hitboxes.length - 1; i >= 0; i--) {
      var b = hitboxes[i];
      if (mx >= b.x && mx <= b.x + b.w && my >= b.y && my <= b.y + b.h) {
        var year = b.ep.start.slice(0, 4);
        var url = new URL(window.location.href); url.searchParams.set('focus_year', year); url.hash = 'ano-foco';
        window.location.href = url.toString(); return;
      }
    }
  });

  // Controles de zoom (décadas)
  var zoom = document.getElementById('life-zoom');
  if (zoom) {
    var all = document.createElement('button'); all.type = 'button'; all.textContent = D.lang === 'en' ? 'All' : 'Tudo'; all.className = 'zoom-btn active';
    all.addEventListener('click', function () { view = { from: y0, to: y1 }; setActive(all); draw(); });
    zoom.appendChild(all);
    for (var dec = Math.floor(y0 / 10) * 10; dec < y1; dec += 10) {
      (function (d0) {
        var b = document.createElement('button'); b.type = 'button'; b.textContent = d0 + 's'; b.className = 'zoom-btn';
        b.addEventListener('click', function () { view = { from: Math.max(y0, d0), to: Math.min(y1, d0 + 10) }; setActive(b); draw(); });
        zoom.appendChild(b);
      })(dec);
    }
  }
  function setActive(btn) { Array.prototype.forEach.call(zoom.querySelectorAll('.zoom-btn'), function (x) { x.classList.toggle('active', x === btn); }); }

  // Filtros
  Array.prototype.forEach.call(document.querySelectorAll('[data-filter-body]'), function (cb) {
    cb.addEventListener('change', function () { filters.bodies[cb.getAttribute('data-filter-body')] = cb.checked; draw(); applyListFilters(); });
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-filter-tone]'), function (cb) {
    cb.addEventListener('change', function () { filters.tones[cb.getAttribute('data-filter-tone')] = cb.checked; draw(); applyListFilters(); });
  });
  var minW = document.getElementById('filter-min-w');
  if (minW) minW.addEventListener('input', function () { filters.minW = parseFloat(minW.value) / 100; var lab = document.getElementById('filter-min-w-label'); if (lab) lab.textContent = minW.value + '%'; draw(); applyListFilters(); });

  function applyListFilters() {
    Array.prototype.forEach.call(document.querySelectorAll('[data-w-body]'), function (li) {
      var ok = filters.bodies[li.getAttribute('data-w-body')] !== false && filters.tones[li.getAttribute('data-w-tone')] !== false &&
        parseFloat(li.getAttribute('data-w-int') || '1') >= filters.minW;
      li.hidden = !ok;
    });
  }

  // Gráfico anual (Chart.js) — total 0–1000 e domínios
  var annualCanvas = document.getElementById('annual-chart');
  if (annualCanvas && window.Chart) {
    var palette = { amber: '#fbbf24', sky: '#38bdf8', cyan: '#22d3ee', rose: '#f43f5e', indigo: '#818cf8', emerald: '#10b981', orange: '#fb923c', purple: '#a855f7' };
    var datasets = D.domains.map(function (d) {
      return { label: d.i + ' ' + d.l, data: D.annual[d.k], borderColor: palette[d.c] || '#94a3b8', backgroundColor: 'transparent', borderWidth: 1.2, pointRadius: 0, tension: 0.3, hidden: true };
    });
    datasets.unshift({ label: D.lang === 'en' ? 'Total intensity (0–1000)' : 'Intensidade total (0–1000)', data: D.annual_total, borderColor: '#f8fafc', backgroundColor: 'rgba(248,250,252,0.08)', fill: true, borderWidth: 2, pointRadius: 0, tension: 0.3 });
    new Chart(annualCanvas, { type: 'line', data: { labels: D.years, datasets: datasets },
      options: { responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false },
        plugins: { legend: { labels: { color: '#94a3b8', boxWidth: 10, font: { size: 10 } } } },
        scales: { x: { ticks: { color: '#94a3b8', maxTicksLimit: 12 }, grid: { color: 'rgba(148,163,184,0.1)' } }, y: { min: 0, max: 1000, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.1)' } } } } });
  }

  window.addEventListener('resize', draw);
  draw();
})();
