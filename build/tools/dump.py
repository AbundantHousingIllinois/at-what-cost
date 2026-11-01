"""Dump each PDF page as positioned, font-annotated text blocks plus link annotations.
Usage: python dump.py <pdf> <prefix> <outdir>
Output per page: <outdir>/<prefix>-pNN.txt
Each block: [B x0,y0,x1,y1] then lines; spans tagged {font size color} when style changes.
Links listed at end with anchor text (text under link rect) and URI / internal page.
"""
import sys, pymupdf
pdf, prefix, out = sys.argv[1:4]
doc = pymupdf.open(pdf)
for i, page in enumerate(doc, 1):
    d = page.get_text("dict")
    lines_out = [f"=== {prefix} PDF page {i} (w={page.rect.width:.0f} h={page.rect.height:.0f}) ==="]
    for b in d["blocks"]:
        if b["type"] != 0:
            x0,y0,x1,y1 = b["bbox"]; lines_out.append(f"[IMAGE {x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f}]"); continue
        x0,y0,x1,y1 = b["bbox"]
        lines_out.append(f"[B {x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f}]")
        for ln in b["lines"]:
            parts=[]; last=None
            for s in ln["spans"]:
                font = s["font"].split("+")[-1]
                tag = (font, round(s["size"],1), f"#{s['color']:06x}")
                if tag != last:
                    parts.append("{%s %s %s}" % tag); last = tag
                parts.append(s["text"])
            lines_out.append("  " + "".join(parts))
    links = page.get_links()
    if links:
        lines_out.append("--- LINKS ---")
        for l in links:
            txt = page.get_textbox(l["from"]).strip().replace("\n"," ")
            tgt = l.get("uri") or (f"internal page {l['page']+1}" if l.get("page") is not None and l.get('page')>=0 else str(l.get('kind')))
            lines_out.append(f"  [{txt}] -> {tgt}")
    open(f"{out}/{prefix}-p{i:02d}.txt","w").write("\n".join(lines_out)+"\n")
print("pages", len(doc))
