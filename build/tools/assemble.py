"""Assemble docs/ pages from extracted fragments + figure manifest.
Run: build/.venv/bin/python build/tools/assemble.py
"""
import json, re, html
from pathlib import Path
from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parents[2]
EX = ROOT / "build" / "extract"
DOCS = ROOT / "docs"
MANIFEST = {f["id"]: f for f in json.loads((ROOT / "build" / "figures-manifest.json").read_text())}
CHARTS = json.loads((DOCS / "assets/data/charts.json").read_text())

MPC_PDF = "downloads/at-what-cost-mpc-zoning-assessment-2026.pdf"
URBAN_PDF = "downloads/urban-institute-zoning-reforms-chicago-2026.pdf"
URBAN_URL = "https://www.urban.org/research/publication/zoning-reforms-could-boost-chicagos-housing-supply"

PAGES = {
    "report/index.html": {
        "title": "At What Cost? How Chicago’s Outdated Zoning and Land Use Systems Thwart Inclusive Growth",
        "short": "Report", "doc": "MPC report",
        "fragments": ["mpc-front", "mpc-housing", "mpc-jobs", "mpc-env", "mpc-process", "mpc-planning", "mpc-conclusion"],
        "pdf": MPC_PDF,
    },
    "report/appendix.html": {
        "title": "Appendices — At What Cost?",
        "short": "Appendices", "doc": "MPC report · Appendices",
        "fragments": ["mpc-appx-additional", "mpc-appx-zoning", "mpc-appx-methodology", "mpc-appx-engagement", "mpc-acknowledgments"],
        "pdf": MPC_PDF,
    },
    "urban/index.html": {
        "title": "Zoning Reforms Could Boost Chicago’s Housing Supply, But Other Investments Are Needed to Ensure Development Benefits All Neighborhoods",
        "short": "Urban Institute analysis", "doc": "Urban Institute article",
        "fragments": ["urban"],
        "pdf": URBAN_PDF,
    },
}

HIDDEN_H2 = {  # sections with no printed heading: navigation-only labels (not shown in body)
    "summary-matrix": "Summary: challenges, visions, and policy recommendations",
    "urban-intro": "Introduction",
    "urban-funders": "Funders and disclaimer",
}

LAST_GROUP = None

TOC_GROUPS = {  # section id -> group label shown above it in the TOC
    "findings-intro": "Research findings & recommendations",
    "conclusion": "",
}


def esc(s):
    return html.escape(s or "", quote=True)


def figure_html(fid, prefix):
    f = MANIFEST.get(fid)
    if not f:
        return f'<!-- missing figure {fid} -->'
    kind = f["kind"]
    if kind == "skip":
        return ""
    title = f.get("title") or ""
    sub = f.get("subtitle") or ""
    head = ""
    if f.get("group_title"):
        global LAST_GROUP
        if f["group_title"] != LAST_GROUP:
            head += f'<p class="fig__group">{esc(f["group_title"])}</p>'
        LAST_GROUP = f["group_title"]
    if title:
        head += f'<p class="fig__title">{esc(title)}</p>'
    if sub:
        head += f'<p class="fig__subtitle">{esc(sub)}</p>'
    tail = ""
    for key, cls in (("caption", "fig-caption"), ("note", "fig-note"), ("source", "fig-source"), ("credit", "credit")):
        v = f.get(key)
        if v:
            tail += f'<p class="{cls}">{esc(v)}</p>'

    def img(src, alt, w=None, h=None, lazy=True):
        dims = f' width="{w}" height="{h}"' if w and h else ""
        return f'<img src="{prefix}{src}" alt="{esc(alt)}"{dims}{" loading=\"lazy\"" if lazy else ""} decoding="async">'

    files = f.get("files") or []
    W, H = f.get("width"), f.get("height")
    if isinstance(W, list):
        sizes = list(zip(W, H))
    elif W:
        sizes = [(W, H)]
    else:
        sizes = []
    alts = f.get("alt") if isinstance(f.get("alt"), list) else [f.get("alt") or ""] * max(1, len(files))
    f = dict(f, alt=alts[0])
    if kind == "chart":
        if fid not in CHARTS:
            return f'<!-- chart {fid} has no data -->'
        extra = ""
        note_site = CHARTS[fid].get("note_site")
        site_note = '<p class="site-note">' + ('Chart made for this site from figures stated in the article text.' if f.get("site_made") else 'Interactive chart redrawn for this site from the figures printed in the source.') + (f' {esc(note_site)}' if note_site else "") + '</p>'
        if f.get("hide_meta"):  # an exact HTML table with the same title, notes and source follows in the text
            return f'<figure class="fig fig--chart" id="fig-{fid}" data-chart="{fid}" data-no-table><div class="fig__media"></div>{site_note}</figure>'
        return f'<figure class="fig fig--chart" id="fig-{fid}" data-chart="{fid}">{head}<div class="fig__media"></div>{tail}{site_note}</figure>'
    if kind == "photo":
        if not files:
            return f'<!-- photo {fid} has no files -->'
        pair = " fig-photo--pair" if len(files) > 1 else ""
        imgs = "".join(f'<div class="fig__media">{img(src, alts[i] if i < len(alts) else "", *(sizes[i] if i < len(sizes) else (None, None)))}</div>' for i, src in enumerate(files))
        cap = tail
        if title and not cap:
            cap = f'<p class="fig-caption">{esc(title)}</p>'
        return f'<figure class="fig-photo" id="fig-{fid}"><div class="{pair.strip()}">{imgs}</div>{cap}</figure>'
    if kind == "image":
        if not files:
            return f'<!-- image {fid} has no files -->'
        w, h = sizes[0] if sizes else (None, None)
        return (f'<figure class="fig fig--image" id="fig-{fid}">{head}<div class="fig__media"><button class="fig__zoom" type="button" aria-label="Enlarge: {esc(title or f.get("alt",""))}">'
                f'{img(files[0], f.get("alt",""), w, h)}</button></div>{tail}</figure>')
    if kind == "image-set":
        panels = f.get("panels") or [str(i) for i in range(len(files))]
        meta = f.get("panel_meta") or []
        titles = f.get("panel_titles") or [m.get("title", "") for m in meta] or panels
        tabs, bodies = [], []
        for i, src in enumerate(files):
            pid = f"{fid}--{panels[i] if i < len(panels) else i}"
            label = titles[i] if i < len(titles) and titles[i] else (panels[i] if i < len(panels) else str(i + 1))
            short = f.get("panel_tabs", [None] * len(files))[i] if f.get("panel_tabs") else label
            tabs.append(f'<button class="chip" role="tab" id="tab-{pid}" aria-controls="panel-{pid}" aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">{esc(short)}</button>')
            pm = meta[i] if i < len(meta) else {}
            ptitle = f'<p class="fig__panel-title">{esc(pm.get("title"))}</p>' if pm.get("title") and pm.get("title") != short else ""
            pcap = "".join(f'<p class="{c}">{esc(pm.get(k))}</p>' for k, c in (("caption", "fig-caption"), ("note", "fig-note"), ("source", "fig-source")) if pm.get(k))
            w, h = sizes[i] if i < len(sizes) else (None, None)
            bodies.append(f'<div class="fig__panel" role="tabpanel" id="panel-{pid}" aria-labelledby="tab-{pid}"{"" if i == 0 else " hidden"}>{ptitle}'
                          f'<div class="fig__media"><button class="fig__zoom" type="button" aria-label="Enlarge: {esc(label)}">{img(src, alts[i] if i < len(alts) else "", w, h)}</button></div>{pcap}</div>')
        return f'<figure class="fig fig--image fig--set" id="fig-{fid}">{head}<div class="fig__tabs" role="tablist">{"".join(tabs)}</div>{"".join(bodies)}{tail}</figure>'
    return f'<!-- unknown kind {kind} -->'


def load_fragment(name):
    p = EX / f"{name}.html"
    if not p.exists():
        print("  !! missing fragment", name)
        return f'<section class="doc-section"><p><em>[Missing content: {name}]</em></p></section>'
    return p.read_text()


def build_page(path, cfg, id_to_page):
    depth = path.count("/")
    prefix = "../" * depth
    body = "\n".join(load_fragment(n) for n in cfg["fragments"])
    soup = BeautifulSoup(body, "html.parser")
    for c in soup.find_all(string=lambda t: isinstance(t, Comment) and t.strip() != "sic"):
        c.extract()
    # cover photo becomes the cover background
    for fig in soup.select("header.doc-cover figure[data-fig]"):
        c = MANIFEST.get(fig["data-fig"], {})
        if c.get("files"):
            fig.replace_with(BeautifulSoup(f'<img class="doc-cover__bg" src="{prefix}{c["files"][0]}" alt="{esc(c.get("alt",""))}">', "html.parser"))
        else:
            fig.decompose()
    # figures
    for fig in soup.select("figure[data-fig]"):
        fid = fig["data-fig"]
        new = BeautifulSoup(figure_html(fid, prefix), "html.parser")
        fig.replace_with(new)
    # charts provide their own table view; drop duplicate <details class="fig-table"> only where a chart precedes it
    for det in soup.select("details.fig-table"):
        prev = det.find_previous_sibling()
        if prev is not None and prev.name == "figure" and prev.has_attr("data-chart"):
            det.decompose()
    # cross-page anchors
    for a in soup.select('a[href^="#"]'):
        target = a["href"][1:]
        tp = id_to_page.get(target)
        if tp and tp != path:
            rel = ("../" * depth) + tp.replace("index.html", "")
            a["href"] = f"{rel}#{target}"
    # TOC
    toc_items = []
    for sec in soup.select("section.doc-section[id]"):
        h = sec.find(["h2"])
        if not h and sec["id"] in HIDDEN_H2:
            h = soup.new_tag("h2", attrs={"class": "visually-hidden"})
            h.string = HIDDEN_H2[sec["id"]]
            sec.insert(0, h)
        if not h:
            continue
        label = re.sub(r"\s+", " ", h.get_text(" ", strip=True))
        subs = []
        for h3 in sec.find_all("h3"):
            if not h3.get("id"):
                h3["id"] = sec["id"] + "--" + re.sub(r"[^a-z0-9]+", "-", h3.get_text().lower()).strip("-")[:50]
            subs.append((h3["id"], re.sub(r"\s+", " ", h3.get_text(" ", strip=True))))
        toc_items.append((sec["id"], label, sec.get("data-section", ""), subs))
    return soup, toc_items, prefix


def toc_html(items, page_path, cfg, prefix):
    out = ['<nav class="toc" id="toc" aria-label="Contents">'
           f'<ul class="toc__site"><li><a href="{prefix}">Home</a></li><li><a href="{prefix}report/">Report</a></li><li><a href="{prefix}report/appendix.html">Appendices</a></li><li><a href="{prefix}urban/">Urban Institute analysis</a></li></ul>'
           '<p class="toc__label">Contents</p><ol>']
    for sid, label, section, subs in items:
        if sid in TOC_GROUPS and TOC_GROUPS[sid]:
            out.append(f'<li class="toc__group">{esc(TOC_GROUPS[sid])}</li>')
        sattr = f' data-section="{section}"' if section else ""
        sub = ""
        if subs and page_path != "report/index.html":
            sub = "<ol>" + "".join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in subs) + "</ol>"
        out.append(f'<li{sattr}><a href="#{sid}">{esc(label)}</a>{sub}</li>')
    out.append("</ol>")
    if page_path == "report/index.html":
        out.append(f'<p class="toc__group">Appendices</p><ol><li><a href="appendix.html">Additional findings, zoning districts, methodology, engagement, acknowledgments →</a></li></ol>')
    if page_path == "report/appendix.html":
        out.append(f'<p class="toc__group">Main report</p><ol><li><a href="./">← Back to the report</a></li></ol>')
    out.append(f'<div class="toc__downloads"><a href="{prefix}{cfg["pdf"]}">Download original PDF ↓</a>')
    if page_path.startswith("urban"):
        out.append(f'<br><a href="{URBAN_URL}">Read on urban.org ↗</a>')
    out.append("</div></nav>")
    return "".join(out)


HEAD = """<!doctype html>
<html lang="en" data-root="{prefix}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="https://abundanthousingillinois.github.io/at-what-cost/assets/img/og-cover.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;700&family=Figtree:ital,wght@0,400;0,600;0,800;0,900;1,400&family=Fraunces:opsz,wght@9..144,300;9..144,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}assets/css/site.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%23e36841'/%3E%3Ctext x='16' y='23' font-size='20' text-anchor='middle' fill='white' font-family='Georgia'%3E%3F%3C/text%3E%3C/svg%3E">
</head>
<body{body_attr}>
<a class="skip-link" href="#main">Skip to content</a>
"""


def header(prefix, current, toc=True):
    nav = [("", "Home", "index.html"), ("report/", "Report", "report/index.html"), ("report/appendix.html", "Appendices", "report/appendix.html"), ("urban/", "Urban Institute analysis", "urban/index.html")]
    links = "".join(
        f'<a href="{prefix}{href}"{" aria-current=\"page\"" if cur == current else ""}{" class=\"hide-sm\"" if label in ("Appendices", "Home") else ""}>{label}</a>'
        for href, label, cur in nav)
    tt = '<button class="toc-toggle" type="button" aria-controls="toc" aria-expanded="false">Contents</button>' if toc else ""
    return f"""<header class="site-header">
{tt}<a class="site-header__brand" href="{prefix}">At What Cost<em>?</em> <span>· Chicago zoning</span></a>
<nav class="site-nav" aria-label="Site">{links}<button class="search-btn" type="button" aria-label="Search">Search <kbd>/</kbd></button></nav>
<div class="progress" aria-hidden="true"></div>
</header>
<dialog class="search-dialog" aria-label="Search"><input type="search" placeholder="Search the report and the Urban Institute article…" aria-label="Search"><ul class="search-results"></ul></dialog>
"""


def footer(prefix):
    return f"""<footer class="site-footer"><div class="site-footer__inner">
<p><strong>About this site.</strong> This is an unofficial, interactive web adaptation of two publications, reproduced in their original wording:
<em>At What Cost? How Chicago’s Outdated Zoning and Land Use Systems Thwart Inclusive Growth</em> (Metropolitan Planning Council, Zoning and Land Use Assessment, October 2026) and
“Zoning Reforms Could Boost Chicago’s Housing Supply, But Other Investments Are Needed to Ensure Development Benefits All Neighborhoods” (Yonah Freemark and Lydia Lo, Urban Institute, October 23, 2026).
All content, findings, figures, and photographs belong to their authors and publishers. Where the two differ, the original PDFs are authoritative.</p>
<p><a href="{prefix}{MPC_PDF}">MPC report (PDF)</a> · <a href="{prefix}{URBAN_PDF}">Urban Institute article (PDF)</a> · <a href="{URBAN_URL}">Article on urban.org</a> · <a href="https://www.metroplanning.org/">metroplanning.org</a></p>
<p>Charts marked “interactive” were redrawn only where the source prints exact values; all other figures are images taken directly from the PDFs.</p>
</div></footer>
"""


def scripts(prefix, charts):
    s = ""
    if charts:
        s += '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js" integrity="sha384-NrKB+u6Ts6AtkIhwPixiKTzgSKNblyhlk0Sohlgar9UHUBzai/sgnNNWWd291xqt" crossorigin="anonymous"></script>\n'
        s += f'<script src="{prefix}assets/js/charts.js" defer></script>\n'
    s += f'<script src="{prefix}assets/js/site.js" defer></script>\n'
    return s


def text_of(el):
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True))


def main():
    # pass 1: map ids -> page
    id_to_page = {}
    for path, cfg in PAGES.items():
        for n in cfg["fragments"]:
            p = EX / f"{n}.html"
            if p.exists():
                for m in re.finditer(r'\sid="([^"]+)"', p.read_text()):
                    id_to_page.setdefault(m.group(1), path)
    search = []
    for path, cfg in PAGES.items():
        print("building", path)
        soup, toc_items, prefix = build_page(path, cfg, id_to_page)
        has_charts = bool(soup.select("figure[data-chart]"))
        # search index entries: each section, split by h3
        for sec in soup.select("section.doc-section[id]"):
            h = sec.find("h2")
            title = text_of(h) if h else sec["id"]
            search.append({"doc": cfg["doc"], "title": title, "url": path.replace("index.html", "") + "#" + sec["id"],
                           "text": text_of(sec)[:20000]})
        cover = ""
        if path == "urban/index.html":
            meta = json.loads((EX / "urban-meta.json").read_text()) if (EX / "urban-meta.json").exists() else {}
            hero = MANIFEST.get("urban-hero", {})
            authors = ", ".join(f'<a href="{esc(a.get("url",""))}">{esc(a["name"])}</a>' if a.get("url") else esc(a["name"]) for a in meta.get("authors", []))
            img = f'<img src="{prefix}{hero["files"][0]}" alt="{esc(hero.get("alt",""))}" width="{hero.get("width","")}" height="{hero.get("height","")}">' if hero.get("files") else ""
            credit = esc(meta.get("hero_credit") or hero.get("credit", ""))
            cover = (f'<header class="article-head" data-section="urban"><p class="article-head__kicker">{esc(meta.get("label","ARTICLE"))}</p>'
                     f'<h1>{esc(meta.get("title", cfg["title"]))}</h1>'
                     f'<p class="article-head__byline">{authors}</p><p class="article-head__date">{esc(meta.get("date",""))}</p>'
                     f'<figure class="article-head__hero">{img}<figcaption class="credit">{credit}</figcaption></figure></header>')
        desc = "Interactive web edition of MPC’s Zoning and Land Use Assessment report “At What Cost?” and the companion Urban Institute analysis of Chicago zoning reforms."
        page = HEAD.format(prefix=prefix, title=esc(cfg["title"]), desc=esc(desc), body_attr="")
        page += header(prefix, path)
        page += f'<div class="doc-layout">{toc_html(toc_items, path, cfg, prefix)}<main id="main" class="doc-main">{cover}{str(soup)}</main></div>'
        page += footer(prefix) + scripts(prefix, has_charts) + "</body></html>\n"
        out = DOCS / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page)
    (DOCS / "assets/data/search-index.json").write_text(json.dumps(search, ensure_ascii=False))
    build_landing(id_to_page)
    print("done")


def build_landing(id_to_page):
    prefix = ""
    matrix = ""
    front = EX / "mpc-front.html"
    if front.exists():
        s = BeautifulSoup(front.read_text(), "html.parser")
        m = s.select_one(".matrix")
        if m:
            for a in m.select('a[href^="#"]'):
                a["href"] = "report/" + a["href"]
            matrix = str(m)
    cover = MANIFEST.get("mpc-p01-cover", {}).get("files", [""])[0]
    urban = MANIFEST.get("urban-hero", {}).get("files", [""])[0]
    page = HEAD.format(prefix=prefix, title="At What Cost? Chicago zoning and land use — interactive edition",
                       desc="Interactive web edition of MPC’s Zoning and Land Use Assessment report “At What Cost?” and the companion Urban Institute analysis of Chicago zoning reforms.", body_attr="")
    page += header(prefix, "index.html", toc=False)
    stats = [
        ("housing", "11%", "“Just 11% of Chicago is zoned for multifamily housing, while 41% is reserved for the most expensive and land-intensive housing type: detached single-family homes.”", "report/#introduction", "MPC report, p. 1"),
        ("housing", "60%", "“60% of new housing built since 2006 has landed in just five community areas, while 45 of Chicago’s 77 community areas have added fewer than 500 new homes in nearly two decades.”", "report/#introduction", "MPC report, p. 1"),
        ("jobs", "14.7 vs 8.6", "“majority-white census tracts average 14.7 businesses per 1,000 residents, compared to just 8.6 in majority-Black tracts”", "report/#introduction", "MPC report, p. 1"),
        ("env", "50%", "“Latinx Chicagoans make up 50% of the population in the top fifth most air-polluted areas”", "report/#introduction", "MPC report, p. 1"),
        ("urban", "9,500", "“We estimate that zoning reforms could enable Chicago to permit up to an additional 9,500 housing units by 2041 above baseline development projections.”", "urban/#urban-intro", "Urban Institute"),
        ("urban", "3.5×", "“Expanding the ADU pilot citywide could have led to 3.5 times as many ADU permits between 2021 and 2025”", "urban/#urban-adu", "Urban Institute"),
    ]
    stat_html = "".join(f'<div class="big-stat" data-section="{s}"><span class="num">{esc(n)}</span><p>{esc(q)}</p><cite><a href="{u}">{esc(c)} →</a></cite></div>' for s, n, q, u, c in stats)
    filt = '<div class="matrix-filter" role="group" aria-label="Filter by challenge"><button class="chip" aria-pressed="true" data-filter="">All five challenges</button>' + "".join(
        f'<button class="chip" data-section="{k}" aria-pressed="false" data-filter="{k}">{v}</button>' for k, v in
        [("housing", "Housing affordability"), ("jobs", "Jobs & business"), ("env", "Pollution & climate"), ("process", "Opaque process"), ("planning", "Citywide planning")]) + "</div>"
    page += f"""<main id="main">
<section class="hero"><img src="{cover}" alt="The Chicago Loop with an elevated train, from the cover of the MPC report"><div class="hero__inner">
<h1>At What Cost?</h1>
<p class="hero__sub">How Chicago’s Outdated Zoning and Land Use Systems Thwart Inclusive Growth</p>
<p><a class="btn" href="report/">Read the report</a><a class="btn btn--ghost" href="urban/">Urban Institute analysis</a></p>
<p class="hero__meta">Metropolitan Planning Council · Zoning and Land Use Assessment · October 2026</p>
</div></section>
<section class="band"><div class="band__inner">
<h2>Two documents, one interactive edition</h2>
<p class="lede">This site presents the full text, figures, and data of MPC’s Zoning and Land Use Assessment report and the Urban Institute’s companion modeling of Chicago zoning reforms, with searchable text, footnote previews, enlargeable maps, and interactive charts.</p>
<div class="doc-cards">
<a class="doc-card" href="report/"><img src="{cover}" alt="" loading="lazy"><div class="doc-card__body"><span class="doc-card__kicker">Report · Metropolitan Planning Council · October 2026</span><h3>At What Cost? How Chicago’s Outdated Zoning and Land Use Systems Thwart Inclusive Growth</h3><p>Five challenges, five visions, and 17 policy recommendations, plus appendices on zoning districts, methodology, and engagement.</p></div></a>
<a class="doc-card" href="urban/"><img src="{urban}" alt="" loading="lazy"><div class="doc-card__body"><span class="doc-card__kicker">Article · Urban Institute · October 23, 2026</span><h3>Zoning Reforms Could Boost Chicago’s Housing Supply, But Other Investments Are Needed to Ensure Development Benefits All Neighborhoods</h3><p>Yonah Freemark and Lydia Lo model four zoning reforms and an expanded ADU policy through 2041.</p></div></a>
</div></div></section>
<section class="band band--paper"><div class="band__inner">
<h2>By the numbers</h2>
<div class="stat-grid">{stat_html}</div>
</div></section>
<section class="band"><div class="band__inner">
<h2>The challenges, the visions, and the policy recommendations</h2>
<p class="lede">The report’s summary table (p. 4). Select a recommendation to read it in context.</p>
{filt}{matrix}
</div></section>
</main>"""
    page += footer(prefix) + scripts(prefix, False) + "</body></html>\n"
    (DOCS / "index.html").write_text(page)


if __name__ == "__main__":
    main()
