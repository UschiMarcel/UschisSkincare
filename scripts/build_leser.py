#!/usr/bin/env python3
"""Baut den lokalen Routine-Leser aus der Seite: gleiche Logik, Produktdaten eingebettet,
echte Bilder aus bilder/<kennung>.jpg (Platzhalter als Fallback). Aufruf: python3 scripts/build_leser.py [--ziel ordner]"""
import json, os, re, shutil, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ziel = sys.argv[sys.argv.index('--ziel') + 1] if '--ziel' in sys.argv else os.path.join(root, '..', 'routine-leser')
ziel = os.path.abspath(ziel)
pd = os.path.join(root, 'produkte')
names = sorted((f for f in os.listdir(pd) if f.endswith('.json') and f != 'dateien.json' and not f.startswith('_')),
               key=lambda x: [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', x)])
files = [json.load(open(os.path.join(pd, n), encoding='utf-8')) for n in names]
auto = {}
ap = os.path.join(pd, '_auto-details.json')
if os.path.exists(ap): auto = json.load(open(ap, encoding='utf-8'))
html = open(os.path.join(root, 'index.html'), encoding='utf-8').read()
qp = os.path.join(root, 'scripts', 'bildquellen.json')
quellen = json.load(open(qp, encoding='utf-8')) if os.path.exists(qp) else {}
imgurl, seen = {}, {}
for r in files:
    for x in (r if isinstance(r, list) else r.get('produkte', [])):
        l = x.get('link') if isinstance(x, dict) else None
        if not l or l in seen: continue
        b = re.sub(r'[^a-z0-9-]+', '-', re.split(r'[?#]', l)[0].rstrip('/').split('/')[-1].lower()).strip('-') or 'produkt'
        k, n = b, 1
        while k in seen.values():
            n += 1; k = '%s-%d' % (b, n)
        seen[l] = k
        if l in quellen: imgurl[k] = quellen[l]
inj = '<script>window.SG_READER=1;window.SG_FILES=%s;window.SG_AUTO=%s;window.SG_IMGURL=%s;</script>\n' % (
    json.dumps(files, ensure_ascii=False).replace('</', '<\\/'), json.dumps(auto, ensure_ascii=False).replace('</', '<\\/'), json.dumps(imgurl))
i = html.index('<script>\n(function(){')
html = html[:i] + inj + html[i:]
html = html.replace('<title>', '<title>Routine-Leser – ', 1)
os.makedirs(os.path.join(ziel, 'bilder'), exist_ok=True)
open(os.path.join(ziel, 'index.html'), 'w', encoding='utf-8').write(html)
pl = os.path.join(ziel, 'bilder', '_platzhalter')
shutil.rmtree(pl, ignore_errors=True)
shutil.copytree(os.path.join(root, 'bilder'), pl, ignore=shutil.ignore_patterns('_layout.json'))
open(os.path.join(ziel, 'LIESMICH.md'), 'w', encoding='utf-8').write(
"""# Routine-Leser (lokal)

1. `index.html` per Doppelklick im Browser öffnen (kein Server nötig).
2. Oben den 6-stelligen Code eingeben. Die Routine erscheint genau wie auf der Seite.
3. Die Produktfotos lädt das Tool beim Öffnen selbst von den Shop-Seiten (Internet nötig). Eigene Fotos haben Vorrang: in den Ordner `bilder/` legen, benannt nach der Kennung (z. B. `balea-cleanser-jelly.jpg`; jpg, jpeg, png, webp, avif). Ohne Foto wird der Platzhalter gezeigt. Die Kennung steht in der Adresse eines Produkts (`#produkt=<kennung>`).
4. Nach neuen Produkten oder Preisen das Tool neu bauen (`python3 scripts/build_leser.py` im Repo). Weicht der Stand ab, zeigt das Tool einen Hinweis.

Nicht ins öffentliche Repo legen.
""")
print('gebaut:', ziel, len(files), 'Dateien')
