# Extraction contract (shared by all extraction agents)

Goal: turn PDF content into **verbatim** HTML fragments that the main thread will drop into page templates.
Faithfulness is the #1 priority. Do not paraphrase, summarize, reorder, "fix" typos, or add words.

## Sources (use in this order)
1. `build/pages/<doc>-pNN.txt` — PyMuPDF dumps: positioned text blocks `[B x0,y0,x1,y1]` with font/size/color tags,
   `[IMAGE ...]` boxes, and a `--- LINKS ---` list (anchor text -> URI). Font tags tell you structure:
   - `ProximaNova-Extrabld 9.0` in a section color = finding lead-in (bold); `ProximaNova-Regular 5.2` = footnote superscript marker;
   - `ProximaNova-Regular 7.5 #4e5154` at page bottom = footnote text; `RegularIt 7.5` = figure captions/notes/sources;
   - `IvyPresto...` = headings/pull quotes; running footer "ZONING AND LAND USE ASSESSMENT • OCTOBER 2026 | n" = DROP.
2. The PDF page images: use the Read tool on the PDF with `pages:` to SEE layout and confirm **reading order**.
   Multi-column pages and sidebars: block order in the dump is NOT always reading order. Decide order by looking at the page.
   Text that wraps across columns / pages must be joined into one paragraph (rejoin hyphenated line breaks like "decision-\nmaking" only when the hyphen is a line-break artifact; keep real hyphens like "by-right", "two-to-four").
3. Do NOT use `pdftotext` for prose (it interleaves columns). It's OK for cross-checking tables.

Pull quotes that repeat body text (e.g. large-type "A more equitable land use system...") are separate elements — emit them once as `.pullquote`, and do not let their fragments contaminate the body paragraphs.

## Output files (write into `build/extract/`)
- `<name>.html` — HTML fragment (no <html>/<head>/<body>). UTF-8. Use real characters (’ “ ” — – • µ ¼).
- `<name>.coverage.json` — `{"pdf": "...", "pages": [..], "figures_placed": [ids], "footnotes": [nums], "notes": ["anything uncertain, typos kept, judgment calls"]}`

## Markup vocabulary (use exactly these classes; nothing else needs styling)
Sections:
```html
<section id="kebab-id" class="doc-section" data-section="housing|jobs|env|process|planning|front|appendix" data-pdf-page="12">
  <h2>Exact heading text</h2>  <!-- h2 for TOC-level headings, h3 below, h4 below that -->
```
Use stable, short ids, e.g. `introduction`, `way-forward`, `summary-matrix`, `expect`, `about-assessment`, `what-is-zoning`,
`how-conducted`, `findings-intro`, `housing-challenge`, `housing-vision`, `planned-developments`, `jobs-challenge`, `jobs-vision`,
`env-challenge`, `env-vision`, `process-challenge`, `process-vision`, `planning-challenge`, `planning-vision`, `conclusion`,
`appx-additional`, `appx-zoning-districts`, `appx-methodology`, `appx-engagement`, `acknowledgments`.

Printed page markers (lets readers cite the PDF): `<span class="pg" data-printed="12" data-pdf="14"></span>` at the point each new PDF page begins.

Challenge / vision banners:
```html
<div class="banner banner--challenge" data-section="housing"><span class="banner__kicker">The challenge:</span> <span class="banner__text">A worsening affordability crisis is pinching budgets and displacing Chicagoans</span></div>
<div class="banner banner--vision" data-section="housing"><span class="banner__kicker">The vision:</span> <span class="banner__text">Make space for more homes that Chicagoans can afford</span></div>
```
(Banners REPLACE the h2 for those sections: put `<h2 class="visually-hidden">The challenge: …</h2>` right before the banner so the TOC works.)

Research finding (» paragraphs): `<p class="finding"><strong class="finding__lead">Bold lead sentence.</strong> Rest of paragraph…</p>`
Plain paragraphs: `<p>`; paragraph-level bold lead-ins in regular prose: `<p><strong>…</strong> …</p>`.
Recommendation (gear-check icon):
```html
<div class="rec" id="rec-legalize-4-flats"><p class="rec__head"><strong class="rec__title">Legalize 4-flats and ADUs citywide:</strong> <span class="rec__summary">At minimum, allow …</span></p>
  <p>body paragraphs that follow…</p></div>
```
Rec ids (use these exact ids, kebab of title): rec-legalize-4-flats, rec-legalize-6-stories, rec-decrease-pd-reliance, rec-deep-affordability,
rec-mix-of-uses, rec-pedestrian-streets, rec-small-business, rec-modern-industry, rec-cumulative-impacts, rec-permeable-surfaces,
rec-climate-vulnerable, rec-modernize-special-uses, rec-reassess-relief, rec-centralize-info, rec-close-data-gaps,
rec-periodic-updates, rec-public-input.

Sidebars/boxes: `<aside class="sidebar" data-kind="glossary|spotlight|box|about">` with `<h4 class="sidebar__title">` inside.
- Glossary ("Terms you'll see in this section"): `<aside class="sidebar" data-kind="glossary"><h4 class="sidebar__title">…</h4><dl class="glossary"><dt data-term="affordable">affordable</dt><dd>…</dd>…</dl></aside>`
- City Spotlight(s): `data-kind="spotlight"`; inside, each city as `<div class="spotlight__item"><h5><a href="…">Portland, OR</a></h5><p>…</p></div>` when the source lists cities, otherwise plain paragraphs.
Big-number stat callouts: `<div class="callout-stat"><p>…<span class="num">60%</span> … <span class="num">5</span> …</p></div>` (keep exact wording).
Pull quotes: `<blockquote class="pullquote"><p>…</p></blockquote>`.
Lists: normal `<ul>/<ol>`.
Tables: `<div class="table-wrap"><table class="data-table"><caption>exact title</caption><thead>…</thead><tbody>…</tbody></table></div>` + notes as `<p class="fig-note">`.

Figures — placeholders only, the main thread inserts images/charts:
```html
<figure class="fig" data-fig="mpc-p13-afford-maps"></figure>
```
Use ONLY ids from `build/figures-manifest.json`. If you find a figure missing from the manifest, invent an id in the same
pattern, add it to `notes` in coverage.json with page + verbatim title/caption/source.
Do not transcribe chart titles/captions/sources into the body — they live in the manifest. (Exception: if a caption appears
in the manifest incorrectly or incompletely, report the correct verbatim text in `notes`.)

Footnotes — GLOBAL numbering exactly as printed (MPC 1–26):
- In text: `<sup class="fnref"><a href="#fn-6" id="fnref-6">6</a></sup>`
- At the end of each fragment (or each section if you prefer): `<ol class="footnotes"><li id="fn-6" value="6">text with <a href="…">links</a> <a href="#fnref-6" class="fn-back">↩</a></li></ol>`
- If a footnote marker appears twice (repeated number), give the second ref id `fnref-6b`.

Links: every link in the `--- LINKS ---` list must become an `<a href>` on the corresponding anchor text. Internal PDF links
(“internal page N”) → `href="#section-id"` of the target section (best guess; note it). External links get no target attr (JS adds it).

Typos: keep as printed. Add `<!-- sic -->` after obvious typos and list them in coverage notes.
Credits like "illustration: Lucie Van der Elst" or photo captions: keep, as `<p class="credit">` or inside figure manifest notes.

Report when done: files written, page coverage, any doubts. Keep the final message short (< 300 words); the files are the deliverable.
