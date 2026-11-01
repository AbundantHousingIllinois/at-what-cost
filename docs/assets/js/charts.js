/* Interactive charts. Data: assets/data/charts.json (values exactly as printed in the source PDFs). */
(async () => {
  const figs = Array.from(document.querySelectorAll("figure[data-chart]"));
  if (!figs.length) return;
  const ROOT = document.documentElement.dataset.root || "./";
  const data = await (await fetch(ROOT + "assets/data/charts.json")).json();

  const INK = "#1d1f22", INK2 = "#4e5154", GRID = "#e7e6e2";
  const FONT = '"Figtree", system-ui, sans-serif';
  if (window.Chart) {
    Chart.defaults.font.family = FONT;
    Chart.defaults.font.size = 12;
    Chart.defaults.color = INK2;
    Chart.defaults.plugins.legend.labels.boxWidth = 12;
    Chart.defaults.plugins.legend.labels.boxHeight = 12;
    Chart.defaults.plugins.tooltip.backgroundColor = "#1d1f22";
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.animation.duration = matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 500;
  }
  const fmt = (v, o = {}) => (o.prefix || "") + (typeof v === "number" ? v.toLocaleString("en-US") : v) + (o.suffix || "");

  // Draws value labels at the end of each bar (selective: one label per bar, text ink not series color)
  const valueLabels = {
    id: "valueLabels",
    afterDatasetsDraw(chart, _args, opts) {
      if (!opts || !opts.enabled) return;
      const { ctx } = chart; ctx.save();
      ctx.font = `600 12px ${FONT}`; ctx.fillStyle = INK;
      const horiz = chart.options.indexAxis === "y";
      chart.data.datasets.forEach((ds, di) => {
        const meta = chart.getDatasetMeta(di); if (meta.hidden) return;
        meta.data.forEach((bar, i) => {
          const v = ds.data[i]; if (!v) return;
          const label = opts.labels ? opts.labels[i] : fmt(v, opts);
          if (horiz) { ctx.textAlign = "left"; ctx.textBaseline = "middle"; ctx.fillText(label, bar.x + 6, bar.y); }
          else { ctx.textAlign = "center"; ctx.textBaseline = "bottom"; ctx.fillText(label, bar.x, bar.y - 4); }
        });
      });
      ctx.restore();
    }
  };

  function tableHTML(headers, rows) {
    return `<div class="table-wrap"><table class="data-table"><thead><tr>${headers.map((h, i) => `<th${i ? ' class="num"' : ""}>${h}</th>`).join("")}</tr></thead><tbody>` +
      rows.map(r => `<tr>${r.map((c, i) => `<td${i ? ' class="num"' : ""}>${c}</td>`).join("")}</tr>`).join("") + "</tbody></table></div>";
  }
  function addTableToggle(fig, html) {
    if (fig.hasAttribute("data-no-table")) { const d = document.createElement("div"); return d; }
    const btn = document.createElement("button");
    btn.type = "button"; btn.className = "chart-table-toggle"; btn.textContent = "View as table"; btn.setAttribute("aria-expanded", "false");
    const box = document.createElement("div"); box.className = "chart-table"; box.hidden = true; box.innerHTML = html;
    btn.addEventListener("click", () => { box.hidden = !box.hidden; btn.textContent = box.hidden ? "View as table" : "Hide table"; btn.setAttribute("aria-expanded", !box.hidden); });
    const anchor = fig.querySelector(".fig__media");
    anchor.after(btn); btn.after(box);
    return box;
  }
  function controls(fig, opts, current, onPick) {
    const bar = document.createElement("div"); bar.className = "chart-controls"; bar.setAttribute("role", "group");
    Object.entries(opts).forEach(([k, label]) => {
      const b = document.createElement("button"); b.type = "button"; b.className = "chip"; b.textContent = label; b.setAttribute("aria-pressed", k === current);
      b.addEventListener("click", () => { bar.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x === b)); onPick(k); });
      bar.appendChild(b);
    });
    fig.querySelector(".fig__media").before(bar);
  }

  function barChart(fig, spec) {
    const media = fig.querySelector(".fig__media");
    const horiz = !!spec.horizontal;
    const n = spec.labels.length;
    media.innerHTML = `<div class="chart-box" style="--chart-h:${horiz ? Math.max(14, n * (spec.datasets && spec.datasets.length > 1 && !spec.datasets[0].stack ? 3.6 : 2.8) + 4) : 22}rem"><canvas role="img"></canvas></div>`;
    const canvas = media.querySelector("canvas");
    let mode = spec.default;
    const cur = () => spec.unit_options ? spec.unit_options[mode] : { datasets: spec.datasets, label: spec.y_label, suffix: spec.unit === "%" ? "%" : "" };
    const stacked = (spec.datasets || []).some(d => d.stack);
    const build = () => {
      const c = cur();
      return c.datasets.map(d => ({
        label: d.label, data: d.data, stack: d.stack,
        backgroundColor: d.colors || d.color, borderColor: "#fff", borderWidth: stacked ? { right: 2 } : 0,
        borderRadius: stacked ? 0 : 4, borderSkipped: "start", maxBarThickness: 46, categoryPercentage: .75, barPercentage: .9
      }));
    };
    const c0 = cur();
    const multi = c0.datasets.length > 1 && !stacked;
    const valueAxis = { beginAtZero: true, stacked, grid: { color: GRID }, border: { display: false },
      ticks: { callback: v => fmt(v, { prefix: "", suffix: cur().suffix && cur().suffix.startsWith("%") ? "%" : "" }) },
      title: { display: !!c0.label, text: c0.label, color: INK2 } };
    const catAxis = { stacked, grid: { display: false }, border: { color: "#9a9a9a" },
      ticks: { autoSkip: false, color: INK, callback(v) { const l = this.getLabelForValue(v); return wrap(l, horiz ? 34 : 16); } } };
    const chart = new Chart(canvas, {
      type: "bar",
      data: { labels: spec.labels, datasets: build() },
      options: {
        indexAxis: horiz ? "y" : "x", responsive: true, maintainAspectRatio: false,
        layout: { padding: { right: horiz ? 56 : 0, top: horiz ? 0 : 18 } },
        scales: horiz ? { x: valueAxis, y: catAxis } : { x: catAxis, y: valueAxis },
        plugins: {
          legend: { display: multi || stacked, position: "top", align: "start", labels: { filter: it => !(stacked && it.text.startsWith("Share of zoned")) } },
          tooltip: { callbacks: { label: ctx => {
            const o = cur(); const v = ctx.raw; if (!v) return null;
            const vl = spec.value_labels && !stacked ? spec.value_labels[ctx.dataIndex] : fmt(v, { prefix: o.prefix, suffix: o.suffix || (spec.unit === "%" ? "%" : "") });
            return `${ctx.dataset.label}: ${vl}`;
          } } },
          valueLabels: { enabled: !stacked, prefix: c0.prefix, suffix: c0.suffix || (spec.unit === "%" ? "%" : ""), labels: spec.value_labels }
        }
      },
      plugins: [valueLabels, ...(stacked && spec.value_labels ? [{ id: "totals", afterDatasetsDraw(ch) {
        const ctx = ch.ctx; ctx.save(); ctx.font = `600 12px ${FONT}`; ctx.fillStyle = INK; ctx.textBaseline = "middle"; ctx.textAlign = "left";
        spec.labels.forEach((_, i) => {
          let maxX = 0, y = 0;
          ch.data.datasets.forEach((d, di) => { const el = ch.getDatasetMeta(di).data[i]; if (d.data[i] && !ch.getDatasetMeta(di).hidden) { maxX = Math.max(maxX, el.x); y = el.y; } });
          if (maxX) ctx.fillText(spec.value_labels[i], maxX + 6, y);
        }); ctx.restore(); } }] : [])]
    });
    const tbl = () => {
      const o = cur();
      if (stacked) return tableHTML(["", "Share of zoned land, 2023"], spec.labels.map((l, i) => [l + (i === 0 ? " (RS 41%, RT 8%, RM 3%)" : ""), spec.value_labels[i]]));
      return tableHTML(["", ...o.datasets.map(d => d.label)], spec.labels.map((l, i) => [l, ...o.datasets.map(d => spec.value_labels && !spec.unit_options ? spec.value_labels[i] : fmt(d.data[i], { prefix: o.prefix, suffix: o.suffix || (spec.unit === "%" ? "%" : "") }))]));
    };
    const box = addTableToggle(fig, tbl());
    canvas.setAttribute("aria-label", fig.querySelector(".fig__title")?.textContent || "chart");
    if (spec.unit_options) controls(fig, spec.toggle_labels, mode, k => {
      mode = k; const o = cur();
      chart.data.datasets = build();
      const axis = horiz ? chart.options.scales.x : chart.options.scales.y;
      axis.title.text = o.label;
      chart.options.plugins.valueLabels = { enabled: true, prefix: o.prefix, suffix: o.suffix };
      chart.update(); box.innerHTML = tbl();
    });
  }

  function stacked100(fig, spec) {
    const media = fig.querySelector(".fig__media");
    media.innerHTML = `<div class="chart-box" style="--chart-h:${spec.labels.length * 3 + 5}rem"><canvas role="img"></canvas></div>`;
    new Chart(media.querySelector("canvas"), {
      type: "bar",
      data: { labels: spec.labels, datasets: spec.datasets.map(d => ({ label: d.label, data: d.data, backgroundColor: d.color, borderColor: "#fff", borderWidth: { right: 2 }, borderSkipped: false, maxBarThickness: 40 })) },
      options: {
        indexAxis: "y", responsive: true, maintainAspectRatio: false,
        scales: { x: { stacked: true, max: 100, grid: { color: GRID }, border: { display: false }, ticks: { callback: v => v + "%" } },
          y: { stacked: true, grid: { display: false }, ticks: { color: INK, autoSkip: false, callback(v) { return wrap(this.getLabelForValue(v), 30); } } } },
        plugins: { legend: { position: "top", align: "start" }, tooltip: { mode: "index", callbacks: { label: c => `${c.dataset.label}: ${c.raw}%` } } }
      },
      plugins: [{ id: "inbar", afterDatasetsDraw(ch) {
        const ctx = ch.ctx; ctx.save(); ctx.font = `600 11px ${FONT}`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ch.data.datasets.forEach((d, di) => ch.getDatasetMeta(di).data.forEach((el, i) => {
          if (d.data[i] >= 6 && !ch.getDatasetMeta(di).hidden) { ctx.fillStyle = di < 4 ? "#fff" : INK; ctx.fillText(d.data[i] + "%", el.x - (el.width / 2), el.y); }
        })); ctx.restore(); } }]
    });
    addTableToggle(fig, tableHTML(["Heat + Flood Susceptibility Quintiles", ...spec.datasets.map(d => d.label)], spec.labels.map((l, i) => [l, ...spec.datasets.map(d => d.data[i] + "%")])));
  }

  function heatgrid(fig, spec) {
    const media = fig.querySelector(".fig__media");
    const max = Math.max(...spec.rows.flatMap(r => r[1]));
    const cell = v => { const a = 0.08 + 0.85 * (v / max); return `<td class="num" style="background:rgba(106,35,16,${a.toFixed(2)});color:${a > .5 ? "#fff" : INK}">${v}%</td>`; };
    media.innerHTML = `<div class="table-wrap"><table class="data-table heatgrid"><thead><tr><th>${spec.row_header}</th>${spec.cols.map(c => `<th class="num">${c}</th>`).join("")}</tr></thead><tbody>` +
      spec.rows.map((r, i) => `<tr><th scope="row" style="border-left:6px solid ${spec.row_colors[i] || "transparent"}">${r[0]}</th>${r[1].map(cell).join("")}</tr>`).join("") + "</tbody></table></div>";
  }

  function waffle(fig, spec) {
    const media = fig.querySelector(".fig__media");
    const cells = [];
    spec.segments.forEach(([name, pct], si) => { for (let i = 0; i < pct; i++) cells.push(`<span data-seg="${si}" title="${name}: ${pct}%"></span>`); });
    for (let i = 0; i < spec.rest; i++) cells.push(spec.rest_label ? `<span title="${spec.rest_label}"></span>` : "<span></span>");
    const total = spec.segments.reduce((s, x) => s + x[1], 0);
    media.innerHTML = `<div class="waffle-wrap"><div class="waffle" role="img" aria-label="${total}% of new units in five community areas">${cells.join("")}</div>
      <div><p class="waffle-big"><span class="num" data-countup>${total}%</span>of the ${spec.total_label}</p>
      <ul class="waffle-legend">${spec.segments.map(([n, p], i) => `<li><button type="button" data-seg="${i}">${n} <strong>${p}%</strong></button></li>`).join("")}</ul>
      <p class="site-note">Each square = 1% of new units. Hover or tap an area to highlight it.</p></div></div>`;
    const w = media.querySelector(".waffle"), big = media.querySelector(".waffle-big .num");
    const focus = i => { w.classList.toggle("is-focused", i !== null); w.querySelectorAll("span[data-seg]").forEach(s => s.classList.toggle("is-on", i !== null && s.dataset.seg == i)); big.textContent = (i === null ? total : spec.segments[i][1]) + "%"; };
    media.querySelectorAll(".waffle-legend button").forEach(b => {
      b.addEventListener("mouseenter", () => focus(+b.dataset.seg)); b.addEventListener("focus", () => focus(+b.dataset.seg));
      b.addEventListener("mouseleave", () => focus(null)); b.addEventListener("blur", () => focus(null));
      b.addEventListener("click", () => focus(+b.dataset.seg));
    });
    addTableToggle(fig, tableHTML(["Community area", "Share of new housing units"], spec.segments.map(([n, p]) => [n, p + "%"])));
  }

  function doughnut(fig, spec) {
    const media = fig.querySelector(".fig__media");
    media.innerHTML = `<div class="chart-box" style="--chart-h:20rem"><canvas role="img"></canvas></div>`;
    const d = spec.datasets[0];
    new Chart(media.querySelector("canvas"), {
      type: "doughnut",
      data: { labels: spec.labels, datasets: [{ data: d.data, backgroundColor: d.colors, borderColor: "#fff", borderWidth: 2 }] },
      options: { responsive: true, maintainAspectRatio: false, cutout: "58%",
        plugins: { legend: { position: "right", labels: { generateLabels: ch => ch.data.labels.map((l, i) => ({ text: `${d.data[i]}% — ${wrap(l, 40).join(" ")}`, fillStyle: d.colors[i], strokeStyle: "#fff", index: i })) } },
          tooltip: { callbacks: { label: c => `${c.raw}%` + (spec.extra && spec.extra[c.dataIndex] ? ` (${spec.extra[c.dataIndex]})` : "") } } } }
    });
    addTableToggle(fig, tableHTML(["Type", "Share"], spec.labels.map((l, i) => [l, d.data[i] + "%"])));
  }

  function wrap(s, n) {
    const words = String(s).split(" "), out = []; let line = "";
    words.forEach(w => { if ((line + " " + w).trim().length > n && line) { out.push(line); line = w; } else line = (line + " " + w).trim(); });
    if (line) out.push(line); return out;
  }

  const io = new IntersectionObserver(entries => entries.forEach(en => {
    if (!en.isIntersecting) return; io.unobserve(en.target);
    const fig = en.target, spec = data[fig.dataset.chart];
    if (!spec) return;
    try {
      ({ bar: barChart, stacked100, heatgrid, waffle, doughnut })[spec.type](fig, spec);
    } catch (e) { console.error("chart failed", fig.dataset.chart, e); }
  }), { rootMargin: "200px" });
  figs.forEach(f => io.observe(f));
})();
