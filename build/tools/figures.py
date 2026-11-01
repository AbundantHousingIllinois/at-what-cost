"""Produce figure images for docs/assets/img from the two source PDFs.

Usage: python figures.py <preview_dir>
Writes <id>.webp (or <id>--<panel>.webp) into docs/assets/img/, a PNG preview of
each into <preview_dir> for visual checking, and prints id/file/size as JSON lines.

Specs:
  ("native", doc, page, xref)            embedded raster, unchanged
  ("clip", doc, page, (x0,y0,x1,y1))     page render of a rect (PDF points) at 220 dpi
  ("clipnotext", doc, page, rect)        same, with all PDF text inside the rect removed first
"""
import io, json, sys
from pathlib import Path
import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/assets/img"
PDFS = {
    "mpc": ROOT / "mpc-ZoningAssessment-Report2026_r1.pdf",
    "urban": ROOT / "Zoning Reforms Could Boost Chicago’s Housing Supply, But Other Investments Are Needed to Ensure Development Benefits All Neighborhoods _ Urban Institute.pdf",
}
DPI = 220

# (id, panel or None, max_width, spec)
FIGS = [
    ("mpc-p03-illustration", None, 1600, ("clipnotext", "mpc", 3, (384, 541, 565, 671))),
    ("mpc-p05-workshop-photos", "1", 1600, ("native", "mpc", 5, 77)),
    ("mpc-p05-workshop-photos", "2", 1600, ("native", "mpc", 5, 79)),
    ("mpc-p09-zine", None, 1600, ("native", "mpc", 9, 178)),
    ("mpc-p11-photos", "1", 1600, ("native", "mpc", 11, 207)),
    ("mpc-p11-photos", "2", 1600, ("native", "mpc", 11, 209)),
    ("mpc-p11-photos", "3", 1600, ("native", "mpc", 11, 211)),
    ("mpc-p13-afford-maps", "renter-citywide", 1800, ("clip", "mpc", 13, (48, 68, 274, 343))),
    ("mpc-p13-afford-maps", "owner-citywide", 1800, ("clip", "mpc", 13, (311, 68, 537, 343))),
    ("mpc-p13-afford-maps", "renter-own-neighborhood", 1800, ("clip", "mpc", 13, (48, 409, 274, 684))),
    ("mpc-p13-afford-maps", "owner-own-neighborhood", 1800, ("clip", "mpc", 13, (311, 409, 537, 684))),
    ("mpc-p14-afford-bars", None, 1800, ("clip", "mpc", 14, (48, 136, 561, 301))),
    ("mpc-p15-structure-map", None, 1800, ("clip", "mpc", 15, (48, 73, 301, 375))),
    ("mpc-p15-capacity-map", None, 1800, ("clip", "mpc", 15, (312, 73, 565, 374))),
    ("mpc-p16-permits-map", None, 1800, ("clip", "mpc", 16, (48, 321, 563, 641))),
    # bar chart is the right half of the same raster as the permits map
    ("mpc-p16-permits-bars", None, 1800, ("clip", "mpc", 16, (296, 420, 563, 640.5))),
    ("mpc-p21-ped-streets-map", None, 1800, ("native", "mpc", 21, 326)),
    # chart-kind entries whose content exists only as a raster: native image as fallback
    ("mpc-p21-business-zoning-grid", None, 1800, ("native", "mpc", 21, 330)),
    ("mpc-p27-heatflood-table", None, 1800, ("native", "mpc", 27, 422)),
    ("mpc-p23-pm25-map", None, 1800, ("clip", "mpc", 23, (337, 410, 554.5, 691))),
    ("mpc-p24-pollution-map", None, 1800, ("clip", "mpc", 24, (48, 72, 287, 385))),
    ("mpc-p24-tree-map", None, 1800, ("clip", "mpc", 24, (325, 72, 564, 385))),
    ("mpc-p25-mfg-map", None, 1800, ("clip", "mpc", 25, (48, 221, 298, 528))),
    ("mpc-p25-mfg-pollution-bar", None, 1800, ("clip", "mpc", 25, (316, 224, 558, 366))),
    ("mpc-p25-mfg-pollution-line", None, 1800, ("clip", "mpc", 25, (312, 418, 564, 556))),
    ("mpc-p26-climate-maps", "heat", 1800, ("clip", "mpc", 26, (48, 397, 209, 595))),
    ("mpc-p26-climate-maps", "flood", 1800, ("clip", "mpc", 26, (225, 397, 386, 595))),
    ("mpc-p26-climate-maps", "combined", 1800, ("clip", "mpc", 26, (401, 397, 563, 595))),
    ("mpc-p27-tree-illustration", None, 1600, ("clipnotext", "mpc", 27, (421, 586, 563.4, 719.6))),
    ("mpc-p35-usi-map", None, 1800, ("clip", "mpc", 35, (48, 329, 305, 663))),
    ("mpc-p36-density-map", None, 1800, ("clip", "mpc", 36, (48, 67, 293, 385))),
    ("mpc-p36-typology-map", None, 1800, ("clip", "mpc", 36, (311, 67, 561, 389))),
    ("mpc-p37-insurance-map", None, 1800, ("clip", "mpc", 37, (48, 132, 256, 340))),
    ("mpc-p37-food-maps", None, 1800, ("clip", "mpc", 37, (48, 403, 564, 645))),
    ("mpc-p38-food-bars", None, 1800, ("clip", "mpc", 38, (48, 71, 562, 309))),
    ("mpc-p41-zoning-map", None, 1800, ("clip", "mpc", 41, (48, 64, 561, 738))),
    ("urban-hero", None, 1600, ("native", "urban", 1, 6)),
    ("urban-fig1", None, 1800, ("native", "urban", 5, 57)),
    ("urban-fig2", None, 1800, ("native", "urban", 7, 63)),
    ("urban-fig3", "reform-1", 1800, ("native", "urban", 10, 75)),
    ("urban-fig3", "reform-2", 1800, ("native", "urban", 11, 78)),
    ("urban-fig3", "reform-3", 1800, ("native", "urban", 12, 81)),
    ("urban-fig3", "reform-4", 1800, ("native", "urban", 13, 84)),
]

_docs = {}
def doc(name):
    if name not in _docs:
        _docs[name] = pymupdf.open(PDFS[name])
    return _docs[name]

def pix_to_pil(pix):
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

def render(spec):
    kind, dname, pno = spec[:3]
    d = doc(dname)
    if kind == "native":
        info = d.extract_image(spec[3])
        im = Image.open(io.BytesIO(info["image"]))
        if im.mode == "CMYK" or info.get("cs-name", "").startswith("DeviceCMYK"):
            # let MuPDF handle colour conversion
            im = pix_to_pil(pymupdf.Pixmap(pymupdf.csRGB, pymupdf.Pixmap(d, spec[3])))
        return im.convert("RGB")
    rect = pymupdf.Rect(spec[3])
    if kind == "clip":
        return pix_to_pil(d[pno - 1].get_pixmap(clip=rect, dpi=DPI, alpha=False))
    if kind == "clipnotext":
        tmp = pymupdf.open()
        tmp.insert_pdf(d, from_page=pno - 1, to_page=pno - 1)
        page = tmp[0]
        for b in page.get_text("dict")["blocks"]:
            if b["type"] == 0 and pymupdf.Rect(b["bbox"]).intersects(rect):
                for ln in b["lines"]:
                    for s in ln["spans"]:
                        page.add_redact_annot(s["bbox"])
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                              graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
        return pix_to_pil(page.get_pixmap(clip=rect, dpi=DPI, alpha=False))
    raise ValueError(kind)

def save(im, name, max_w, preview_dir):
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    im.save(OUT / name, "WEBP", quality=85, method=6)
    pv = im.copy(); pv.thumbnail((1000, 1000))
    pv.save(Path(preview_dir) / (Path(name).stem + ".png"))
    return im.size

def cover(preview_dir):
    """MPC cover photo without the title text and the MPC logo (vector), plus og-cover.jpg."""
    tmp = pymupdf.open()
    tmp.insert_pdf(doc("mpc"), from_page=0, to_page=0)
    page = tmp[0]
    page.add_redact_annot(pymupdf.Rect(330, 45, 575, 152))   # title + subtitle text
    page.add_redact_annot(pymupdf.Rect(194, 694, 418, 749))  # MPC logo paths
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                          graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED)
    im = pix_to_pil(page.get_pixmap(dpi=200, alpha=False))
    size = save(im, "mpc-p01-cover.webp", 1600, preview_dir)
    # og image: 1200x630 band through the middle of the photo (L tracks + buildings)
    w = 1200; s = w / im.width
    big = im.resize((w, round(im.height * s)), Image.LANCZOS)
    top = round(big.height * 0.40)
    og = big.crop((0, top, w, top + 630))
    og.save(OUT / "og-cover.jpg", "JPEG", quality=85, optimize=True)
    og.copy().save(Path(preview_dir) / "og-cover.png")
    return size

if __name__ == "__main__":
    preview = sys.argv[1]
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[2:])
    results = []
    if not only or "mpc-p01-cover" in only:
        w, h = cover(preview)
        results.append({"id": "mpc-p01-cover", "panel": None, "file": "assets/img/mpc-p01-cover.webp", "width": w, "height": h})
    for fid, panel, max_w, spec in FIGS:
        if only and fid not in only:
            continue
        name = f"{fid}--{panel}.webp" if panel else f"{fid}.webp"
        w, h = save(render(spec), name, max_w, preview)
        results.append({"id": fid, "panel": panel, "file": f"assets/img/{name}", "width": w, "height": h})
    for r in results:
        print(json.dumps(r))
