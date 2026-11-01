/* At What Cost? — site interactions. No dependencies. */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const ROOT = document.documentElement.dataset.root || "./";

  // External links open in a new tab
  $$('a[href^="http"]').forEach(a => {
    if (!a.host || a.host !== location.host) { a.target = "_blank"; a.rel = "noopener"; }
  });

  // ---------- Progressive disclosure ----------
  // Bold lead sentences stay visible; the rest of the paragraph (and recommendation bodies) expand on click.
  // All text remains in the HTML (search, print, no-JS readers get everything).
  const main = $(".doc-main");
  const toggles = [];
  function setOpen(t, open) {
    t.host.classList.toggle("is-open", open);
    t.btn.setAttribute("aria-expanded", open);
  }
  function makeToggle(host, btn) {
    btn.classList.add("lead-toggle");
    btn.setAttribute("role", "button");
    btn.tabIndex = 0;
    btn.setAttribute("aria-expanded", "false");
    const t = { host, btn };
    btn.addEventListener("click", e => { if (e.target.closest("a")) return; setOpen(t, !host.classList.contains("is-open")); });
    btn.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); btn.click(); } });
    toggles.push(t);
  }
  if (main) {
    const skip = ".sidebar, .callout-stat, .pullquote, .fig, .footnotes, .matrix, .card, .rec__head, table, .timeline, li, .doc-cover, .article-head";
    $$("p", main).forEach(p => {
      if (p.closest(skip)) return;
      const lead = p.firstElementChild;
      if (!lead || lead.tagName !== "STRONG") return;
      // lead must be the first meaningful node
      let n = p.firstChild;
      while (n && n !== lead && n.nodeType === 3 && !n.data.trim()) n = n.nextSibling;
      if (n !== lead) return;
      const rest = [];
      for (let m = lead.nextSibling; m; m = m.nextSibling) rest.push(m);
      const restText = rest.map(m => m.textContent).join("").trim();
      if (restText.length < 40) return;
      const more = document.createElement("span");
      more.className = "more";
      rest.forEach(m => more.appendChild(m));
      p.appendChild(more);
      p.classList.add("collapsible");
      makeToggle(p, lead);
    });
    $$(".rec", main).forEach(rec => {
      const head = $(".rec__head", rec);
      if (!head) return;
      const rest = Array.from(rec.children).filter(c => c !== head);
      if (!rest.length) return;
      const more = document.createElement("div");
      more.className = "more";
      rest.forEach(c => more.appendChild(c));
      rec.appendChild(more);
      rec.classList.add("collapsible");
      makeToggle(rec, head);
    });
  }
  // open collapsed text when something inside it is targeted (footnote back-links, deep links)
  function revealTarget(id) {
    const el = id && document.getElementById(id);
    const host = el && el.closest(".collapsible");
    if (!host) return;
    const t = toggles.find(x => x.host === host);
    if (t) setOpen(t, true);
  }
  revealTarget(decodeURIComponent(location.hash.slice(1)));
  window.addEventListener("hashchange", () => revealTarget(decodeURIComponent(location.hash.slice(1))));
  document.addEventListener("click", e => {
    const a = e.target.closest('a[href*="#"]');
    if (a && a.pathname === location.pathname) revealTarget(decodeURIComponent(a.hash.slice(1)));
  });
  // page-wide switch, remembered between visits
  if (toggles.length && $(".toc")) {
    const KEY = "awc-full-text";
    const sw = document.createElement("button");
    sw.type = "button"; sw.className = "full-text-switch";
    const apply = on => {
      document.body.classList.toggle("show-all", on);
      sw.setAttribute("aria-pressed", on);
      sw.innerHTML = `<span class="full-text-switch__track" aria-hidden="true"></span> Show full text`;
    };
    let on = localStorage.getItem(KEY) === "1";
    apply(on);
    sw.addEventListener("click", () => { on = !on; localStorage.setItem(KEY, on ? "1" : "0"); apply(on); });
    $(".toc__label").before(sw);
  }

  // ---------- TOC: scrollspy + progress + mobile toggle ----------
  const toc = $(".toc");
  const progress = $(".progress");
  const tocLinks = toc ? $$('a[href^="#"]', toc) : [];
  const targets = tocLinks.map(a => document.getElementById(decodeURIComponent(a.hash.slice(1)))).filter(Boolean);
  let ticking = false;
  function onScroll() {
    ticking = false;
    const y = window.scrollY + window.innerHeight * 0.25;
    let current = null;
    for (const t of targets) { if (t.getBoundingClientRect().top + window.scrollY <= y) current = t; }
    tocLinks.forEach(a => a.classList.toggle("is-active", current && a.hash === "#" + current.id));
    const sec = current && current.closest("[data-section]");
    if (sec) document.body.dataset.section = sec.dataset.section; else delete document.body.dataset.section;
    if (progress) {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      progress.style.width = (h > 0 ? (window.scrollY / h) * 100 : 0) + "%";
    }
    const active = toc && $(".is-active", toc);
    if (active && toc.scrollHeight > toc.clientHeight && window.innerWidth > 960) {
      const r = active.getBoundingClientRect(), tr = toc.getBoundingClientRect();
      if (r.top < tr.top + 40 || r.bottom > tr.bottom - 40) toc.scrollTop += r.top - tr.top - tr.height / 3;
    }
  }
  window.addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  onScroll();
  const tocBtn = $(".toc-toggle");
  if (tocBtn && toc) {
    tocBtn.addEventListener("click", () => { const o = toc.classList.toggle("is-open"); tocBtn.setAttribute("aria-expanded", o); });
    toc.addEventListener("click", e => { if (e.target.closest("a")) { toc.classList.remove("is-open"); tocBtn.setAttribute("aria-expanded", "false"); } });
  }

  // ---------- Popovers (footnotes + glossary) ----------
  let pop = null;
  function closePop() { if (pop) { pop.remove(); pop = null; } }
  function openPop(anchor, html) {
    closePop();
    pop = document.createElement("div");
    pop.className = "popover"; pop.setAttribute("role", "tooltip"); pop.innerHTML = html;
    document.body.appendChild(pop);
    const r = anchor.getBoundingClientRect();
    const w = pop.offsetWidth;
    let left = Math.min(window.scrollX + r.left - 20, window.scrollX + document.documentElement.clientWidth - w - 12);
    pop.style.left = Math.max(window.scrollX + 8, left) + "px";
    pop.style.top = (window.scrollY + r.bottom + 8) + "px";
    pop.addEventListener("mouseleave", closePop);
  }
  $$(".fnref a").forEach(a => {
    const li = document.getElementById(a.hash.slice(1));
    if (!li) return;
    const html = `<span class="popover__num">${li.getAttribute("value") || a.textContent}</span>${li.innerHTML}`;
    a.addEventListener("mouseenter", () => openPop(a, html));
    a.addEventListener("focus", () => openPop(a, html));
    a.addEventListener("click", e => { if (matchMedia("(hover: none)").matches && !pop) { e.preventDefault(); openPop(a, html); } });
  });
  document.addEventListener("click", e => { if (pop && !e.target.closest(".popover, .fnref, dfn.term")) closePop(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") closePop(); });

  // Glossary: mark the first later use of each defined term (text unchanged; adds a hover definition)
  $$('.glossary').forEach(dl => {
    const scope = dl.closest(".doc-section");
    if (!scope) return;
    $$("dt", dl).forEach(dt => {
      const term = dt.textContent.replace(/:$/, "").trim();
      const dd = dt.nextElementSibling; if (!dd) return;
      const re = new RegExp("\\b" + term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b", "i");
      const blocks = $$("p, li", scope).filter(p => !p.closest(".sidebar, .fig, .footnotes, .rec__head"));
      for (const p of blocks) {
        const walker = document.createTreeWalker(p, NodeFilter.SHOW_TEXT);
        let node, done = false;
        while ((node = walker.nextNode())) {
          if (node.parentElement.closest("a, dfn, strong")) continue;
          const m = node.data.match(re);
          if (!m) continue;
          const after = node.splitText(m.index); after.splitText(m[0].length);
          const d = document.createElement("dfn"); d.className = "term"; d.tabIndex = 0;
          d.textContent = after.data; after.replaceWith(d);
          const html = `<strong>${dt.innerHTML}</strong> ${dd.innerHTML}`;
          d.addEventListener("mouseenter", () => openPop(d, html));
          d.addEventListener("focus", () => openPop(d, html));
          d.addEventListener("click", () => openPop(d, html));
          done = true; break;
        }
        if (done) break;
      }
    });
  });

  // ---------- Lightbox ----------
  const lb = document.createElement("div");
  lb.className = "lightbox"; lb.hidden = true; lb.setAttribute("role", "dialog"); lb.setAttribute("aria-modal", "true");
  lb.innerHTML = '<button class="lightbox__close" type="button">Close ✕</button><img alt="">';
  document.body.appendChild(lb);
  let lbReturn = null;
  const closeLb = () => { lb.hidden = true; document.body.style.overflow = ""; lbReturn && lbReturn.focus(); };
  lb.addEventListener("click", e => { if (e.target === lb || e.target.closest(".lightbox__close")) closeLb(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !lb.hidden) closeLb(); });
  $$(".fig__zoom").forEach(btn => btn.addEventListener("click", () => {
    const img = $("img", btn);
    $("img", lb).src = img.dataset.full || img.currentSrc || img.src; $("img", lb).alt = img.alt;
    lbReturn = btn; lb.hidden = false; document.body.style.overflow = "hidden"; $(".lightbox__close", lb).focus();
  }));

  // ---------- Tabs (image sets) ----------
  $$(".fig__tabs").forEach(tabs => {
    const buttons = $$("[role=tab]", tabs);
    buttons.forEach((b, i) => {
      b.addEventListener("click", () => select(i));
      b.addEventListener("keydown", e => {
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
          const n = (i + (e.key === "ArrowRight" ? 1 : -1) + buttons.length) % buttons.length;
          select(n); buttons[n].focus();
        }
      });
    });
    function select(i) {
      buttons.forEach((b, j) => {
        b.setAttribute("aria-selected", i === j); b.tabIndex = i === j ? 0 : -1;
        document.getElementById(b.getAttribute("aria-controls")).hidden = i !== j;
      });
    }
  });

  // ---------- Filterable tables ----------
  $$("table[data-filterable]").forEach(table => {
    const rows = $$("tbody tr", table);
    const bar = document.createElement("div");
    bar.className = "table-filter";
    const cats = [...new Set(rows.map(r => r.dataset.category).filter(Boolean))];
    bar.innerHTML = `<input type="search" placeholder="Filter rows…" aria-label="Filter table rows">` +
      (cats.length ? `<button class="chip" aria-pressed="true" data-cat="">All</button>` + cats.map(c => `<button class="chip" aria-pressed="false" data-cat="${c}">${c}</button>`).join("") : "") +
      `<span class="count"></span>`;
    (table.closest(".table-wrap") || table).before(bar);
    const input = $("input", bar), count = $(".count", bar);
    let cat = "";
    function apply() {
      const q = input.value.trim().toLowerCase(); let n = 0;
      rows.forEach(r => { const show = (!q || r.textContent.toLowerCase().includes(q)) && (!cat || r.dataset.category === cat); r.hidden = !show; if (show) n++; });
      count.textContent = `${n} of ${rows.length} rows`;
    }
    input.addEventListener("input", apply);
    $$("[data-cat]", bar).forEach(b => b.addEventListener("click", () => {
      cat = b.dataset.cat; $$("[data-cat]", bar).forEach(x => x.setAttribute("aria-pressed", x === b)); apply();
    }));
    apply();
  });

  // ---------- Timeline filter ----------
  $$(".timeline-legend").forEach(legend => {
    const tl = legend.parentElement.querySelector(".timeline") || $(".timeline");
    if (!tl) return;
    const items = $$(":scope > li", legend);
    items.forEach(li => {
      const type = li.dataset.type; if (!type) return;
      const b = document.createElement("button");
      b.className = "chip"; b.dataset.type = type; b.setAttribute("aria-pressed", "true"); b.innerHTML = li.innerHTML;
      li.innerHTML = ""; li.appendChild(b);
      b.addEventListener("click", () => {
        b.setAttribute("aria-pressed", b.getAttribute("aria-pressed") !== "true");
        const on = $$("button[aria-pressed=true]", legend).map(x => x.dataset.type);
        $$(":scope > li", tl).forEach(item => item.hidden = !on.includes(item.dataset.type));
      });
    });
  });

  // ---------- Recommendation matrix filter ----------
  $$(".matrix-filter").forEach(bar => {
    const matrix = bar.nextElementSibling;
    $$("button", bar).forEach(b => b.addEventListener("click", () => {
      $$("button", bar).forEach(x => x.setAttribute("aria-pressed", x === b));
      const s = b.dataset.filter;
      $$(".matrix__row[data-section]", matrix).forEach(r => r.hidden = s && r.dataset.section !== s);
    }));
  });

  // ---------- Count-up numbers ----------
  const counters = $$("[data-countup]");
  if (counters.length && "IntersectionObserver" in window && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const io = new IntersectionObserver(entries => entries.forEach(en => {
      if (!en.isIntersecting) return; io.unobserve(en.target);
      const el = en.target, final = el.textContent, m = final.match(/[\d,.]+/);
      if (!m) return;
      const target = parseFloat(m[0].replace(/,/g, "")), dec = (m[0].split(".")[1] || "").length, t0 = performance.now();
      const fmt = v => v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec });
      (function step(t) {
        const p = Math.min(1, (t - t0) / 900), e = 1 - Math.pow(1 - p, 3);
        el.textContent = final.replace(m[0], fmt(target * e));
        if (p < 1) requestAnimationFrame(step); else el.textContent = final;
      })(t0);
    }), { threshold: 0.6 });
    counters.forEach(c => io.observe(c));
  }

  // ---------- Search ----------
  const dlg = $(".search-dialog");
  const openBtn = $(".search-btn");
  if (dlg && openBtn) {
    const input = $("input", dlg), list = $(".search-results", dlg);
    let index = null, active = -1;
    async function load() {
      if (index) return index;
      const res = await fetch(ROOT + "assets/data/search-index.json"); index = await res.json(); return index;
    }
    function esc(s) { return s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
    function render(q) {
      list.innerHTML = ""; active = -1;
      if (!q || q.length < 2) return;
      const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
      const hits = [];
      for (const e of index) {
        const low = e.text.toLowerCase();
        if (!terms.every(t => low.includes(t) || e.title.toLowerCase().includes(t))) continue;
        let score = terms.reduce((s, t) => s + (e.title.toLowerCase().includes(t) ? 5 : 0) + (low.split(t).length - 1), 0);
        hits.push([score, e]);
      }
      hits.sort((a, b) => b[0] - a[0]);
      if (!hits.length) { list.innerHTML = `<li class="search-empty">No matches for “${esc(q)}”.</li>`; return; }
      const re = new RegExp("(" + terms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|") + ")", "gi");
      hits.slice(0, 30).forEach(([, e]) => {
        const low = e.text.toLowerCase(); const i = Math.max(0, low.indexOf(terms[0]) - 70);
        const snip = (i > 0 ? "…" : "") + e.text.slice(i, i + 200) + "…";
        const li = document.createElement("li");
        li.innerHTML = `<a href="${ROOT}${e.url}"><span class="r-doc">${esc(e.doc)}</span><span class="r-title">${esc(e.title)}</span><span class="r-snip">${esc(snip).replace(re, "<mark>$1</mark>")}</span></a>`;
        list.appendChild(li);
      });
    }
    const open = async () => { dlg.showModal(); input.focus(); input.select(); await load(); render(input.value.trim()); };
    openBtn.addEventListener("click", open);
    document.addEventListener("keydown", e => {
      if ((e.key === "/" && !e.target.closest("input, textarea")) || (e.key === "k" && (e.metaKey || e.ctrlKey))) { e.preventDefault(); open(); }
    });
    input.addEventListener("input", async () => { await load(); render(input.value.trim()); });
    input.addEventListener("keydown", e => {
      const links = $$("a", list);
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault(); active = (active + (e.key === "ArrowDown" ? 1 : -1) + links.length) % links.length;
        links.forEach((l, i) => l.classList.toggle("is-active", i === active)); links[active] && links[active].scrollIntoView({ block: "nearest" });
      } else if (e.key === "Enter" && links.length) { (links[active] || links[0]).click(); dlg.close(); }
    });
    list.addEventListener("click", e => { if (e.target.closest("a")) dlg.close(); });
    dlg.addEventListener("click", e => { if (e.target === dlg) dlg.close(); });
  }
})();
