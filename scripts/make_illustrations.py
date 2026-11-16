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


def label(x, y, w, h, accent):
    """Neutrales Etikett: Punkt und zwei Linien, keine Schrift."""
    cx = x + w / 2
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#fff" opacity=".9"/>'
        f'<circle cx="{cx}" cy="{y + h * .28:.1f}" r="{min(w, h) * .11:.1f}" fill="{accent}"/>'
        f'<rect x="{x + w * .2:.1f}" y="{y + h * .52:.1f}" width="{w * .6:.1f}" height="4" rx="2" fill="#2b2a27" opacity=".55"/>'
        f'<rect x="{x + w * .3:.1f}" y="{y + h * .68:.1f}" width="{w * .4:.1f}" height="4" rx="2" fill="#2b2a27" opacity=".3"/>'
    )


def shape(kind, body, cap, accent):
    dark = shade(body, -0.12)
    shine = '<rect x="{x}" y="{y}" width="8" height="{h}" rx="4" fill="#fff" opacity=".28"/>'
    if kind == "pump":
        return (
            f'<rect x="105" y="150" width="90" height="180" rx="26" fill="{body}"/>'
            + shine.format(x=114, y=166, h=130)
            + f'<rect x="138" y="126" width="24" height="28" fill="{dark}"/>'
            f'<rect x="128" y="114" width="44" height="16" rx="5" fill="{cap}"/>'
            f'<rect x="145" y="86" width="10" height="32" fill="{cap}"/>'
            f'<rect x="116" y="68" width="68" height="22" rx="9" fill="{cap}"/>'
            f'<rect x="176" y="74" width="30" height="9" rx="4.5" fill="{cap}"/>'
            + label(118, 206, 64, 86, accent)
        )
    if kind == "tube":
        stripes = "".join(f'<line x1="{x}" y1="84" x2="{x}" y2="112" stroke="{shade(body, -.25)}" stroke-width="2" opacity=".5"/>' for x in range(104, 200, 8))
        return (
            f'<path d="M110 292 Q150 302 190 292 L206 112 L94 112 Z" fill="{body}"/>'
            f'<path d="M122 290 L108 116 L124 116 L132 292 Z" fill="#fff" opacity=".22"/>'
            f'<rect x="90" y="82" width="120" height="32" rx="4" fill="{dark}"/>' + stripes
            + f'<rect x="130" y="288" width="40" height="14" fill="{dark}"/>'
            f'<rect x="116" y="300" width="68" height="32" rx="7" fill="{cap}"/>'
            + label(116, 150, 68, 96, accent)
        )
    if kind == "jar":
        ridges = "".join(f'<line x1="{x}" y1="196" x2="{x}" y2="230" stroke="#000" stroke-width="2" opacity=".12"/>' for x in range(94, 212, 9))
        return (
            f'<rect x="88" y="232" width="124" height="98" rx="26" fill="{body}"/>'
            + shine.format(x=98, y=246, h=64)
            + f'<rect x="80" y="188" width="140" height="48" rx="12" fill="{cap}"/>' + ridges
            + label(100, 258, 100, 54, accent)
        )
    if kind == "tin":
        return (
            f'<rect x="74" y="276" width="152" height="56" rx="16" fill="{body}"/>'
            f'<rect x="68" y="240" width="164" height="44" rx="14" fill="{cap}"/>'
            f'<circle cx="150" cy="262" r="12" fill="{accent}" opacity=".9"/>'
            f'<rect x="86" y="292" width="128" height="6" rx="3" fill="#fff" opacity=".35"/>'
        )
    if kind == "dropper":
        return (
            f'<rect x="108" y="172" width="84" height="158" rx="22" fill="{body}"/>'
            f'<rect x="108" y="172" width="84" height="158" rx="22" fill="#fff" opacity=".12"/>'
            + shine.format(x=118, y=188, h=110)
            + f'<rect x="136" y="150" width="28" height="26" fill="{dark}"/>'
            f'<rect x="126" y="128" width="48" height="28" rx="7" fill="{cap}"/>'
            f'<path d="M139 130 L139 92 Q139 62 150 62 Q161 62 161 92 L161 130 Z" fill="{cap}"/>'
            f'<rect x="144" y="76" width="5" height="40" rx="2.5" fill="#fff" opacity=".25"/>'
            + label(118, 208, 64, 88, accent)
        )
    if kind == "flip":
        return (
            f'<rect x="106" y="132" width="88" height="198" rx="30" fill="{body}"/>'
            + shine.format(x=116, y=150, h=140)
            + f'<rect x="134" y="112" width="32" height="24" fill="{dark}"/>'
            f'<rect x="120" y="76" width="60" height="42" rx="11" fill="{cap}"/>'
            f'<rect x="120" y="96" width="60" height="3" fill="#fff" opacity=".2"/>'
            + label(118, 190, 64, 100, accent)
        )
    # padjar
    return (
        f'<rect x="92" y="152" width="116" height="178" rx="22" fill="{body}"/>'
        + shine.format(x=102, y=168, h=130)
        + f'<rect x="84" y="114" width="132" height="44" rx="11" fill="{cap}"/>'
        + label(104, 196, 92, 100, accent)
    )


def svg(slug, name, step):
    circ, body, cap = PALETTE.get(step, DEFAULT)
    # pro Produkt leicht abweichende Farbe, damit nicht alles gleich aussieht
    seed = int(hashlib.md5(slug.encode()).hexdigest()[:6], 16)
    dh = ((seed % 13) - 6) / 360
    dl = (((seed // 13) % 7) - 3) / 100
    circ, body = shade(circ, dl / 2, dh), shade(body, dl, dh)
    accent = shade(body, -0.22)
    k = form(name, step)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 380" role="img" aria-label="Illustration">'
        '<ellipse cx="150" cy="334" rx="70" ry="6" fill="#000" opacity=".12"/>'
        + shape(k, body, cap, accent)
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
