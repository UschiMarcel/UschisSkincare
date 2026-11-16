#!/usr/bin/env python3
"""Erzeugt für jedes Produkt eine einfache, allgemeine Illustration (SVG) nach Produktart.

Aufruf:  python scripts/make_illustrations.py [--produkte produkte] [--ziel bilder] [--ueberschreiben]

Es werden keine echten Verpackungen nachgebildet: Je nach Schritt und Namen entsteht eine neutrale
Flasche, Tube, Dose oder Pipettenflasche in einer Pastellfarbe, ohne Hintergrund, Marken, Logos oder Aufschriften.
Dateiname = Kennung des Produkts (letzter Teil des Links), z. B. bilder/mighty-melt.svg.
Vorhandene Dateien bleiben unverändert, außer mit --ueberschreiben. Eigene Bilder gehen immer vor:
trage im Produkt "bild": "bilder/mein-foto.jpg" ein.
"""
import argparse, colorsys, glob, hashlib, json, os, re

# Pastellfarben je Schritt: Kreis, Behälter, Verschluss
PALETTE_ALT = {
    "Reinigungs-Öle": ("#f8e0b4", "#eab968", "#2b2a27"),
    "Reinigungs-Cleanser": ("#dbe9d6", "#b4d2ab", "#33423a"),
    "Peeling": ("#f9d8cb", "#f09c7e", "#2b2a27"),
    "Toner": ("#d8e7f1", "#a8c9de", "#2b2a27"),
    "Serum": ("#e8dff2", "#c9b4e2", "#2b2a27"),
    "Retinol / Anti-Aging": ("#ecdccd", "#86563b", "#1f1f1d"),
    "Creme": ("#f5eadb", "#fbf6ee", "#bfa67f"),
    "Salbe": ("#f6eec9", "#f1de8e", "#3a3a36"),
    "Sonnenschutz": ("#fcdcb9", "#f5b072", "#2b2a27"),
}
DEFAULT = ("#e6e2d8", "#cfc9bb", "#2b2a27")


def slugs(ordner):
    """Gleiche Regel wie die Seite: letzter Teil des Links, klein, nur a-z 0-9 und Bindestrich."""
    prod = {}
    for f in sorted(glob.glob(os.path.join(ordner, "*.json")), key=lambda x: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", os.path.basename(x))]):
        n = os.path.basename(f)
        if n.startswith("_") or n == "dateien.json":
            continue
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for p in data if isinstance(data, list) else data.get("produkte", []):
            if p.get("link"):
                prod.setdefault(p["link"], {}).update(p)
    seen, out = {}, []
    for link, p in prod.items():
        if p.get("aktiv") is False:
            continue
        b = re.sub(r"[^a-z0-9-]+", "-", re.split(r"[?#]", link)[0].rstrip("/").split("/")[-1].lower()).strip("-") or "produkt"
        k, n = b, 1
        while k in seen:
            n += 1
            k = f"{b}-{n}"
        seen[k] = 1
        out.append((k, p))
    return out


ALIAS = {"reinigung": "Reinigungs-Cleanser", "reinigung-cleanser": "Reinigungs-Cleanser", "cleanser": "Reinigungs-Cleanser",
         "öl": "Reinigungs-Öle", "oel": "Reinigungs-Öle", "reinigungsöl": "Reinigungs-Öle", "retinol": "Retinol / Anti-Aging",
         "anti-aging": "Retinol / Anti-Aging", "aha": "Peeling", "salben": "Salbe"}


def norm_step(step):
    t = (step or "").strip()
    return ALIAS.get(t.lower(), t)


def form(name, step):
    """Verpackungsform nach dem, was die Händlerseiten beschreiben (Tube, Dose, Sprühflasche, Pipette …)."""
    step = norm_step(step)
    n = (name or "").lower()
    if "liquid hydration" in n:
        return "spray"          # weiße Sprühflasche, 110 ml
    if re.search(r"balsam|balm|melt", n):
        return "jar"            # Glastiegel (Deckel in lila Stahl-Optik, siehe svg())
    if "happier barrier" in n or re.search(r"\bvas\b", n) or "zero feel" in n:
        return "tube"           # Tuben
    if step == "Reinigungs-Öle":
        return "pump"
    if step == "Reinigungs-Cleanser":
        return "tube"           # Balea Beauty Expert Cleanser: Tuben
    if step in ("Peeling", "Serum", "Retinol / Anti-Aging"):
        return "tube" if re.search(r"creme|cream", n) else "dropper"
    if step == "Toner":
        return "flip"
    if step == "Creme":
        return "pump" if re.search(r"lotion|fluid", n) else "jar"
    if step == "Sonnenschutz":
        return "pump" if "fluid" in n else "tube"
    return "tube" if step == "Salbe" else "jar"


def shade(hexcol, dl=0.0, dh=0.0):
    h = hexcol.lstrip("#")
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    hh = (hh + dh) % 1
    l = max(0, min(1, l + dl))
    r, g, b = colorsys.hls_to_rgb(hh, l, s)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def hexa(c, dl=0.0):
    return shade(c, dl)


FARBEN = [  # (Stichwort im Link/Namen, Farbe) – grobe Annäherung, mit dem Feld "farbe" im Produkt überschreibbar
    ("arganoel", "#e8b45a"), ("jelly", "#8fd6c8"), ("balea-peeling-cleanser", "#a8e0cf"), ("happier-barrier", "#f3c9a8"), ("cordes", "#efe6d8"), ("mighty-melt", "#f4dcae"), ("cleansing-balm", "#cfe9de"),
    ("balea-peeling", "#8fd6bd"), ("balea", "#9bdcc6"),
    ("c-glow", "#f5a95e"), ("a-game", "#e59aa8"), ("apad", "#cdb7e8"), ("happier-barrier", "#f3d3d6"),
    ("zero-feel", "#f6dfb0"), ("liquid-hydration", "#bfdcef"), ("geek-und-gorgeous", "#f0c2cc"),
    ("aha-peeling", "#f2a27f"), ("120h", "#9ccbe8"), ("niacinamid", "#c2aee3"), ("isana", "#a9d3ec"),
    ("zinksalbe", "#cfe3f1"), ("panthenol", "#f1de8e"), ("cordes", "#e8d0b2"),
]
STEPFARBE = {"Sonnenschutz": "#f6dfb0", "Creme": "#f3e6dc", "Serum": "#cdb7e8", "Toner": "#bfdcef", "Salbe": "#f1de8e"}


def farbe(slug, name, step, vorgabe=None):
    if vorgabe:
        return vorgabe
    key = (slug + " " + (name or "")).lower()
    for k, c in FARBEN:
        if k in key:
            return c
    return STEPFARBE.get(step, "#d9d6cb")


def gdefs(col, lid=None):
    lg = ""
    if lid:
        lg = (f'<linearGradient id="lp" x1="0" x2="1"><stop offset="0" stop-color="{shade(lid, -.3)}"/><stop offset=".2" stop-color="{shade(lid, .05)}"/><stop offset=".42" stop-color="{shade(lid, .3)}"/><stop offset=".62" stop-color="{shade(lid, -.08)}"/><stop offset=".85" stop-color="{shade(lid, .14)}"/><stop offset="1" stop-color="{shade(lid, -.34)}"/></linearGradient>')
    return (
        "<defs>" + lg +
        f'<linearGradient id="fg" x1="0" x2="1"><stop offset="0" stop-color="#cfd2cd"/><stop offset=".08" stop-color="#eceeea"/><stop offset=".5" stop-color="#f7f8f5"/><stop offset=".9" stop-color="#e3e5e0"/><stop offset="1" stop-color="#c3c6c0"/></linearGradient>'
        f'<linearGradient id="lq" x1="0" x2="1"><stop offset="0" stop-color="{shade(col, -.14)}"/><stop offset=".35" stop-color="{shade(col, .06)}"/><stop offset=".7" stop-color="{col}"/><stop offset="1" stop-color="{shade(col, -.18)}"/></linearGradient>'
        '<linearGradient id="mt" x1="0" x2="1"><stop offset="0" stop-color="#7d8083"/><stop offset=".18" stop-color="#d9dbdd"/><stop offset=".42" stop-color="#f6f7f8"/><stop offset=".62" stop-color="#b4b7ba"/><stop offset=".85" stop-color="#e3e5e7"/><stop offset="1" stop-color="#6f7275"/></linearGradient>'
        '<linearGradient id="bk" x1="0" x2="1"><stop offset="0" stop-color="#0c0c0c"/><stop offset=".3" stop-color="#4a4a4a"/><stop offset=".6" stop-color="#1a1a1a"/><stop offset="1" stop-color="#050505"/></linearGradient>'
        '<radialGradient id="sh" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#000" stop-opacity=".34"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>'
        '<filter id="bl" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="1.8"/></filter>'
        "</defs>"
    )


def brushed(x, y, w, h, n=18):
    g = w / n
    return "".join(f'<rect x="{x + i * g + g / 2:.1f}" y="{y}" width=".8" height="{h}" fill="#fff" opacity="{.35 if i % 3 else .1}"/>' for i in range(n))


def silver(x, y, w, h, r=3, fill="url(#mt)"):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>' + brushed(x, y, w, h)
            + f'<rect x="{x}" y="{y}" width="{w}" height="2.5" rx="1.2" fill="#fff" opacity=".7"/>'
            f'<rect x="{x}" y="{y + h - 2.5}" width="{w}" height="2.5" fill="#000" opacity=".18"/>')


def frosted(cx, w, y0, y1, fill_top, r=10):
    """Mattierter Glaszylinder: milchiges Glas, Flüssigkeit in Produktfarbe, dicker Boden."""
    l = cx - w / 2
    h = y1 - y0
    return (
        f'<clipPath id="fc"><rect x="{l}" y="{y0}" width="{w}" height="{h}" rx="{r}"/></clipPath>'
        f'<rect x="{l}" y="{y0}" width="{w}" height="{h}" rx="{r}" fill="url(#fg)"/>'
        f'<g clip-path="url(#fc)">'
        f'<rect x="{l + 5}" y="{fill_top}" width="{w - 10}" height="{y1 - fill_top - 17}" rx="7" fill="url(#lq)" opacity=".92"/>'
        f'<rect x="{l + 5}" y="{fill_top}" width="{w - 10}" height="{y1 - fill_top - 17}" rx="7" fill="#fff" opacity=".28"/>'
        f'<ellipse cx="{cx}" cy="{fill_top + 1}" rx="{w / 2 - 6}" ry="3" fill="#fff" opacity=".45"/>'
        f'<rect x="{l}" y="{y1 - 18}" width="{w}" height="18" fill="#fff" opacity=".55"/>'
        f'<rect x="{l}" y="{y1 - 18}" width="{w}" height="1.5" fill="#000" opacity=".1"/>'
        f'<rect x="{l + 6}" y="{y0 + 14}" width="7" height="{h - 36}" rx="3.5" fill="#fff" opacity=".7" filter="url(#bl)"/>'
        f'<rect x="{l + w - 12}" y="{y0 + 18}" width="4" height="{h - 44}" rx="2" fill="#fff" opacity=".4" filter="url(#bl)"/>'
        "</g>"
        f'<rect x="{l}" y="{y0}" width="{w}" height="{h}" rx="{r}" fill="none" stroke="#9a9d97" stroke-opacity=".35"/>'
    )


def shape(kind, col, lid=None):
    cx = 150
    if kind == "pump":
        s = frosted(cx, 100, 160, 330, 196)
        s += silver(cx - 31, 118, 62, 44, 4) + silver(cx - 27, 100, 54, 20, 3)
        s += silver(cx - 24, 52, 48, 50, 4)
        s += f'<path d="M{cx - 24} 58 L{cx - 46} 58 Q{cx - 52} 58 {cx - 52} 64 L{cx - 52} 70 L{cx - 24} 70 Z" fill="url(#mt)"/>'
        return s
    if kind == "dropper":
        s = frosted(cx, 96, 170, 330, 204)
        s += f'<rect x="{cx - 2.5}" y="176" width="5" height="136" rx="2.5" fill="#fff" opacity=".35"/>'
        s += silver(cx - 28, 138, 56, 34, 4)
        s += f'<path d="M{cx - 16} 140 L{cx - 16} 92 Q{cx - 16} 58 {cx} 58 Q{cx + 16} 58 {cx + 16} 92 L{cx + 16} 140 Z" fill="url(#bk)"/>'
        s += f'<rect x="{cx - 10}" y="72" width="4" height="56" rx="2" fill="#fff" opacity=".4" filter="url(#bl)"/>'
        return s
    if kind == "spray":
        l = cx - 48
        s = (
            f'<rect x="{l}" y="150" width="96" height="180" rx="14" fill="url(#fg)"/>'
            f'<rect x="{l}" y="262" width="96" height="46" fill="{col}" opacity=".85"/>'
            f'<rect x="{l + 6}" y="166" width="7" height="150" rx="3.5" fill="#fff" opacity=".7" filter="url(#bl)"/>'
            f'<rect x="{l}" y="150" width="96" height="180" rx="14" fill="none" stroke="#9a9d97" stroke-opacity=".35"/>'
        )
        s += f'<rect x="{cx - 30}" y="118" width="60" height="36" rx="5" fill="url(#fg)" stroke="#9a9d97" stroke-opacity=".4"/>'
        s += f'<rect x="{cx - 20}" y="84" width="40" height="36" rx="6" fill="url(#fg)" stroke="#9a9d97" stroke-opacity=".4"/>'
        s += f'<path d="M{cx - 20} 90 L{cx - 38} 90 Q{cx - 42} 90 {cx - 42} 94 L{cx - 42} 100 L{cx - 20} 100 Z" fill="url(#fg)" stroke="#9a9d97" stroke-opacity=".4"/>'
        return s
    if kind == "flip":
        s = frosted(cx, 98, 150, 330, 190)
        s += silver(cx - 34, 96, 68, 58, 6)
        return s
    if kind == "jar":
        s = frosted(cx, 140, 238, 330, 262, 20)
        s += silver(cx - 74, 194, 148, 46, 8, "url(#lp)" if lid else "url(#mt)")
        return s
    if kind == "padjar":
        s = frosted(cx, 124, 168, 330, 214, 22)
        s += silver(cx - 68, 124, 136, 48, 8)
        return s
    if kind == "tin":
        return (
            f'<rect x="{cx - 84}" y="284" width="168" height="46" rx="12" fill="url(#mt)"/>' + brushed(cx - 84, 284, 168, 46, 30)
            + f'<rect x="{cx - 88}" y="246" width="176" height="44" rx="12" fill="url(#mt)"/>' + brushed(cx - 88, 246, 176, 44, 30)
            + f'<rect x="{cx - 80}" y="251" width="160" height="4" rx="2" fill="#fff" opacity=".7" filter="url(#bl)"/>'
            f'<rect x="{cx - 88}" y="285" width="176" height="3" fill="#000" opacity=".3"/>'
        )
    # Tube
    body = f'<path d="M104 296 Q150 306 196 296 L212 112 L88 112 Z" fill="url(#lq)"/>'
    return (
        body
        + '<path d="M118 294 L102 118 L116 118 L128 296 Z" fill="#fff" opacity=".35" filter="url(#bl)"/>'
        + '<rect x="84" y="82" width="132" height="32" rx="5" fill="url(#lq)"/><rect x="84" y="82" width="132" height="32" rx="5" fill="#000" opacity=".12"/>'
        + "".join(f'<rect x="{x}" y="86" width="1.6" height="26" fill="#000" opacity=".18"/>' for x in range(96, 206, 6))
        + f'<rect x="{cx - 34}" y="298" width="68" height="36" rx="6" fill="url(#fg)" stroke="#9a9d97" stroke-opacity=".45"/>'
    )


def svg(slug, name, step, vorgabe=None):
    step = norm_step(step)
    k = form(name, step)
    col = farbe(slug, name, step, vorgabe)
    lid = "#8a63c9" if re.search(r"balsam|balm|melt", (name or "").lower()) else None
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 380" role="img" aria-label="Illustration">'
        + gdefs(col, lid)
        + '<ellipse cx="150" cy="334" rx="92" ry="11" fill="url(#sh)"/>'
        + shape(k, col, lid)
        + "</svg>\n"
    )


# Beschriftungsfläche je Form in Prozent des Bildes: (links, Mitte oben, Breite)
LABELBOX = {"pump": (35.5, 62, 30), "dropper": (35.5, 63, 30), "flip": (35.5, 60, 30), "spray": (35.5, 63, 30),
            "jar": (33, 77, 36), "padjar": (33, 68, 34), "tin": (33, 78, 36), "tube": (36.5, 56, 27)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--produkte", default="produkte")
    ap.add_argument("--ziel", default="bilder")
    ap.add_argument("--ueberschreiben", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.ziel, exist_ok=True)
    n = 0
    layout = {}
    for slug, p in slugs(a.produkte):
        layout[slug] = LABELBOX[form(p.get("name", ""), p.get("schritt", ""))]
        f = os.path.join(a.ziel, slug + ".svg")
        if os.path.exists(f) and not a.ueberschreiben:
            continue
        open(f, "w", encoding="utf-8").write(svg(slug, p.get("name", ""), p.get("schritt", ""), p.get("farbe")))
        n += 1
        print("✓", f, "(", form(p.get("name", ""), p.get("schritt", "")), ")")
    json.dump(layout, open(os.path.join(a.ziel, "_layout.json"), "w"))
    print(n, "Illustrationen erstellt")


if __name__ == "__main__":
    main()
