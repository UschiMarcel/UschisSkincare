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
PALETTE = {
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


def form(name, step):
    n = (name or "").lower()
    if "pad" in n:
        return "padjar"
    if re.search(r"balsam|balm|melt", n):
        return "tin"
    if step == "Reinigungs-Öle":
        return "pump"
    if step == "Reinigungs-Cleanser":
        return "pump" if re.search(r"jelly|gel", n) else "tube"
    if step in ("Peeling", "Serum", "Retinol / Anti-Aging"):
        return "dropper"
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


def gdefs(body, capk):
    """Gemeinsame Verläufe: Glas, Flüssigkeit, Verschluss, Metall, Schatten, Weichzeichner."""
    g = (hexa(body, -.30), hexa(body, -.10), hexa(body, .10), hexa(body, .16), hexa(body, -.04), hexa(body, -.34))
    caps = {
        "black": ("#050505", "#3b3b3b", "#161616", "#000"),
        "white": ("#bfbdb6", "#ffffff", "#e8e6df", "#a9a79f"),
        "gold": ("#7d6232", "#e9cf92", "#b8975a", "#6b5127"),
    }[capk]
    return (
        "<defs>"
        f'<linearGradient id="gl" x1="0" x2="1"><stop offset="0" stop-color="{g[0]}"/><stop offset=".14" stop-color="{g[1]}"/><stop offset=".38" stop-color="{g[2]}"/><stop offset=".55" stop-color="{g[3]}"/><stop offset=".82" stop-color="{g[4]}"/><stop offset="1" stop-color="{g[5]}"/></linearGradient>'
        f'<linearGradient id="lq" x1="0" x2="1"><stop offset="0" stop-color="{hexa(body, -.38)}"/><stop offset=".4" stop-color="{hexa(body, -.12)}"/><stop offset="1" stop-color="{hexa(body, -.42)}"/></linearGradient>'
        f'<linearGradient id="cp" x1="0" x2="1"><stop offset="0" stop-color="{caps[0]}"/><stop offset=".28" stop-color="{caps[1]}"/><stop offset=".6" stop-color="{caps[2]}"/><stop offset="1" stop-color="{caps[3]}"/></linearGradient>'
        '<linearGradient id="mt" x1="0" x2="1"><stop offset="0" stop-color="#8a8c8e"/><stop offset=".25" stop-color="#f4f5f6"/><stop offset=".5" stop-color="#b9bbbd"/><stop offset=".78" stop-color="#eceeef"/><stop offset="1" stop-color="#7d7f82"/></linearGradient>'
        '<radialGradient id="sh" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#000" stop-opacity=".38"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>'
        '<filter id="bl" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.6"/></filter>'
        "</defs>"
    )


def bottle_path(cx, w, nw, ny, ys, yb, r=18):
    l, rr, nl, nr = cx - w / 2, cx + w / 2, cx - nw / 2, cx + nw / 2
    return (f"M{nl} {ny} L{nl} {ys} C{nl} {ys + 16} {l} {ys + 6} {l} {ys + 40} L{l} {yb - r} Q{l} {yb} {l + r} {yb} "
            f"L{rr - r} {yb} Q{rr} {yb} {rr} {yb - r} L{rr} {ys + 40} C{rr} {ys + 6} {nr} {ys + 16} {nr} {ys} L{nr} {ny} Z")


def glass(cx, w, nw, ny, ys, yb, fill=.62, milk=False):
    """Glaskörper mit Flüssigkeit, Reflexen und dickem Boden."""
    d = bottle_path(cx, w, nw, ny, ys, yb)
    top = yb - (yb - ys) * fill
    l, rr = cx - w / 2, cx + w / 2
    o = (
        f'<clipPath id="bc"><path d="{d}"/></clipPath>'
        f'<path d="{d}" fill="url(#gl)"/>'
        f'<g clip-path="url(#bc)">'
        f'<rect x="{l}" y="{top:.1f}" width="{w}" height="{yb - top + 2:.1f}" fill="url(#lq)" opacity="{.96 if milk else .85}"/>'
        f'<ellipse cx="{cx}" cy="{top:.1f}" rx="{w / 2}" ry="3.2" fill="#fff" opacity=".28"/>'
        f'<rect x="{l}" y="{yb - 11}" width="{w}" height="12" fill="#000" opacity=".26"/>'
        f'<rect x="{l + 7}" y="{ys + 26}" width="7" height="{yb - ys - 54}" rx="3.5" fill="#fff" opacity=".6" filter="url(#bl)"/>'
        f'<rect x="{rr - 13}" y="{ys + 36}" width="3.5" height="{yb - ys - 70}" rx="1.7" fill="#fff" opacity=".3" filter="url(#bl)"/>'
        f'<path d="M{l + 12} {ys + 18} Q{cx - 8} {ys + 4} {cx + 4} {ys + 10}" stroke="#fff" stroke-width="3" fill="none" opacity=".45" filter="url(#bl)"/>'
        f'<rect x="{l}" y="{ys + 40}" width="{w}" height="{yb - ys - 40}" fill="none" stroke="#000" stroke-opacity=".18" stroke-width="2"/>'
        "</g>"
    )
    return o


def ribs(x, y, w, h, n, op=.22):
    gap = w / n
    return "".join(f'<rect x="{x + i * gap + gap / 2 - .6:.1f}" y="{y}" width="1.2" height="{h}" fill="#000" opacity="{op}"/>' for i in range(n))


def cap_block(x, y, w, h, r=6, fill="url(#cp)"):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>'
            f'<rect x="{x + 5}" y="{y + 2}" width="3.2" height="{h - 4}" rx="1.6" fill="#fff" opacity=".35" filter="url(#bl)"/>')


def shape(kind, body, capk):
    cx = 150
    if kind == "dropper":
        s = glass(cx, 96, 40, 176, 200, 330, .66)
        s += f'<rect x="{cx - 3}" y="178" width="6" height="140" rx="3" fill="#fff" opacity=".14"/>'
        s += cap_block(cx - 27, 142, 54, 36, 5) + ribs(cx - 27, 146, 54, 28, 11)
        s += f'<path d="M{cx - 15} 144 L{cx - 15} 96 Q{cx - 15} 62 {cx} 62 Q{cx + 15} 62 {cx + 15} 96 L{cx + 15} 144 Z" fill="url(#cp)"/>'
        s += f'<rect x="{cx - 9}" y="76" width="4" height="56" rx="2" fill="#fff" opacity=".4" filter="url(#bl)"/>'
        return s
    if kind == "pump":
        s = glass(cx, 104, 40, 166, 192, 330, .68)
        s += cap_block(cx - 28, 138, 56, 34, 5) + ribs(cx - 28, 142, 56, 26, 12)
        s += f'<rect x="{cx - 5}" y="104" width="10" height="38" fill="url(#cp)"/>'
        s += cap_block(cx - 30, 80, 60, 26, 8) + f'<path d="M{cx + 28} 86 L{cx + 58} 86 Q{cx + 64} 86 {cx + 64} 92 L{cx + 64} 96 L{cx + 28} 96 Z" fill="url(#cp)"/>'
        s += f'<rect x="{cx - 4}" y="150" width="8" height="150" rx="4" fill="#fff" opacity=".12"/>'
        return s
    if kind == "flip":
        s = glass(cx, 96, 44, 152, 176, 330, .72)
        s += cap_block(cx - 31, 100, 62, 56, 9) + ribs(cx - 31, 108, 62, 40, 13, .18)
        s += f'<rect x="{cx - 31}" y="122" width="62" height="2.5" fill="#000" opacity=".25"/>'
        return s
    if kind == "jar":
        s = (
            f'<clipPath id="jc"><rect x="{cx - 68}" y="236" width="136" height="94" rx="22"/></clipPath>'
            f'<rect x="{cx - 68}" y="236" width="136" height="94" rx="22" fill="url(#gl)"/>'
            f'<g clip-path="url(#jc)"><rect x="{cx - 68}" y="240" width="136" height="90" fill="url(#lq)" opacity=".92"/>'
            f'<rect x="{cx - 68}" y="318" width="136" height="14" fill="#000" opacity=".24"/>'
            f'<rect x="{cx - 56}" y="250" width="8" height="64" rx="4" fill="#fff" opacity=".55" filter="url(#bl)"/>'
            f'<rect x="{cx + 50}" y="254" width="4" height="56" rx="2" fill="#fff" opacity=".28" filter="url(#bl)"/></g>'
        )
        s += cap_block(cx - 72, 190, 144, 52, 10) + ribs(cx - 72, 198, 144, 36, 28, .16)
        s += f'<rect x="{cx - 72}" y="236" width="144" height="3" fill="#000" opacity=".3"/>'
        return s
    if kind == "padjar":
        s = (
            f'<clipPath id="jc"><rect x="{cx - 62}" y="170" width="124" height="160" rx="24"/></clipPath>'
            f'<rect x="{cx - 62}" y="170" width="124" height="160" rx="24" fill="url(#gl)"/>'
            f'<g clip-path="url(#jc)"><rect x="{cx - 62}" y="215" width="124" height="115" fill="url(#lq)" opacity=".85"/>'
            f'<rect x="{cx - 62}" y="318" width="124" height="14" fill="#000" opacity=".24"/>'
            f'<rect x="{cx - 51}" y="190" width="8" height="120" rx="4" fill="#fff" opacity=".55" filter="url(#bl)"/></g>'
        )
        s += cap_block(cx - 66, 128, 132, 48, 10) + ribs(cx - 66, 136, 132, 32, 26, .16)
        return s
    if kind == "tin":
        return (
            f'<rect x="{cx - 84}" y="282" width="168" height="48" rx="12" fill="url(#mt)"/>'
            f'<rect x="{cx - 84}" y="318" width="168" height="12" rx="6" fill="#000" opacity=".18"/>'
            f'<rect x="{cx - 88}" y="244" width="176" height="44" rx="12" fill="url(#cp)"/>'
            f'<rect x="{cx - 80}" y="249" width="160" height="4" rx="2" fill="#fff" opacity=".4" filter="url(#bl)"/>'
            f'<rect x="{cx - 88}" y="282" width="176" height="3" fill="#000" opacity=".35"/>'
        )
    # tube (Kunststoff, matt)
    stripes = "".join(f'<rect x="{x}" y="86" width="1.6" height="26" fill="#000" opacity=".18"/>' for x in range(96, 206, 6))
    return (
        f'<path d="M104 296 Q150 306 196 296 L212 112 L88 112 Z" fill="url(#gl)"/>'
        f'<path d="M118 294 L102 118 L116 118 L128 296 Z" fill="#fff" opacity=".28" filter="url(#bl)"/>'
        f'<rect x="84" y="82" width="132" height="32" rx="5" fill="url(#gl)"/><rect x="84" y="82" width="132" height="32" rx="5" fill="#000" opacity=".12"/>' + stripes
        + cap_block(cx - 36, 296, 72, 38, 7)
    )


def svg(slug, name, step):
    circ, body, capc = PALETTE.get(step, DEFAULT)
    seed = int(hashlib.md5(slug.encode()).hexdigest()[:6], 16)
    dh = ((seed % 13) - 6) / 360
    dl = (((seed // 13) % 7) - 3) / 100
    k = form(name, step)
    base = shade(circ if k in ("jar", "padjar") and step == "Creme" else body, dl, dh)
    capk = "gold" if step in ("Creme", "Toner") else ("white" if k == "tube" else "black")
    if k == "tin":
        capk = "black"
    if step in ("Serum", "Retinol / Anti-Aging", "Reinigungs-Öle", "Sonnenschutz", "Peeling") and k != "tube":
        base = shade(base, -.1)
    if k in ("jar", "padjar"):
        base = shade(base, .2)
    inner = shape(k, base, capk)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 380" role="img" aria-label="Illustration">'
        + gdefs(base, capk)
        + '<ellipse cx="150" cy="334" rx="92" ry="11" fill="url(#sh)"/>'
        + inner
        + "</svg>\n"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--produkte", default="produkte")
    ap.add_argument("--ziel", default="bilder")
    ap.add_argument("--ueberschreiben", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.ziel, exist_ok=True)
    n = 0
    for slug, p in slugs(a.produkte):
        f = os.path.join(a.ziel, slug + ".svg")
        if os.path.exists(f) and not a.ueberschreiben:
            continue
        open(f, "w", encoding="utf-8").write(svg(slug, p.get("name", ""), p.get("schritt", "")))
        n += 1
        print("✓", f, "(", form(p.get("name", ""), p.get("schritt", "")), ")")
    print(n, "Illustrationen erstellt")


if __name__ == "__main__":
    main()
