# At What Cost? — interactive web edition

An unofficial, interactive GitHub Pages adaptation of two publications on Chicago zoning, reproduced in their original wording:

- **At What Cost? How Chicago’s Outdated Zoning and Land Use Systems Thwart Inclusive Growth.** Metropolitan Planning Council (MPC), Zoning and Land Use Assessment, October 2026. File: `docs/downloads/at-what-cost-mpc-zoning-assessment-2026.pdf`.
- **Zoning Reforms Could Boost Chicago’s Housing Supply, But Other Investments Are Needed to Ensure Development Benefits All Neighborhoods.** Yonah Freemark and Lydia Lo, Urban Institute, October 23, 2026. A print of the article from urban.org. File: `docs/downloads/urban-institute-zoning-reforms-chicago-2026.pdf`.

All content, figures, and photographs belong to their authors and publishers. Where the site and the PDFs differ, the PDFs are authoritative. Both PDFs are linked from every page of the site.

## What's on the site

| Page | Content |
|---|---|
| `docs/index.html` | Landing page: both documents, headline statistics (quoted), and the report's recommendations matrix, filterable by challenge |
| `docs/report/` | The full MPC report, pages 1–32, with a sticky table of contents, footnote previews, glossary hovers, and printed page markers |
| `docs/report/appendix.html` | Appendices: additional findings, zoning districts, research methodology (filterable data tables), engagement timeline, and acknowledgments |
| `docs/urban/` | The full Urban Institute article, with an interactive Table 1 and switchable reform maps |

**How the figures are handled:**
- Charts are interactive (Chart.js) **only where the source prints exact values**. Each one has a "View as table" option.
- Charts without printed data labels, and all maps, are images taken directly from the PDFs. You can click them to enlarge.
- To search the full text of both documents, press `/` or use the Search button.
- To keep the report easy to skim, only the bold lead sentence of each paragraph, finding, and recommendation shows at first. Click the lead to open the rest, or turn on **Show full text** in the contents sidebar (the setting is remembered). The full text is always in the HTML, so search, printing, and no-JS readers get everything.

## Run locally

```sh
python3 -m http.server -d docs 8000
# open http://localhost:8000
```

## Publish on GitHub Pages

1. Push the repo to GitHub.
2. Go to **Settings → Pages**. Under **Build and deployment**, choose **Deploy from a branch**.
3. Select branch `main` and folder `/docs`.

The site is static HTML, CSS, and JS, with no build step at serve time.

## How it was built (`build/`)

| Path | What it is |
|---|---|
| `build/tools/dump.py` | Uses PyMuPDF to dump each PDF page (from `docs/downloads/`) as positioned, font-annotated text blocks plus link annotations (`build/pages/`) |
| `build/extract/` | Verbatim HTML fragments per section, extracted from those dumps and checked against the page images. `CONTRACT.md` defines the markup |
| `build/figures-manifest.json` | Every figure's verbatim title, caption, notes, and source, plus its image file(s) |
| `docs/assets/data/charts.json` | The exact values behind the interactive charts |
| `build/tools/assemble.py` | Merges the fragments, figures, and templates into `docs/` and builds the search index |

To rebuild the site:

```sh
python3 -m venv build/.venv && build/.venv/bin/pip install pymupdf pillow beautifulsoup4
build/.venv/bin/python build/tools/assemble.py
```
