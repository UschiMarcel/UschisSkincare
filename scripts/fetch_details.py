#!/usr/bin/env python3
"""Holt Anwendung und Inhaltsstoffe von den Produktseiten und schreibt sie nach produkte/_auto-details.json.

Aufruf:  python scripts/fetch_details.py [--produkte produkte] [--nur-neue]
Benötigt: pip install playwright && playwright install chromium

Von Hand eingetragene Felder in den Produktdateien haben auf der Seite immer Vorrang.
Optional (Umgebungsvariable ANTHROPIC_API_KEY): schreibt eine kurze Zusammenfassung ("details") in eigenen Worten.
"""
import argparse, datetime, glob, json, os, re, sys, urllib.request
from urllib.parse import urlparse

KEYS = {
    "inhaltsstoffe": re.compile(r"^(inhaltsstoffe|zutaten|ingredients|inci)\b", re.I),
    "anwendung": re.compile(r"^(anwendung|anwendungshinweise?|verwendung|gebrauchsanweisung|so wird.?s angewendet)\b", re.I),
    "beschreibung": re.compile(r"^(produktbeschreibung|beschreibung|produktdetails|produktinformationen)\b", re.I),
}

# Läuft im Browser: öffnet Abschnitte und liest den Text unter den passenden Überschriften.
JS = r"""
(keys) => {
  const out = {};
  const rx = {};
  for (const k in keys) rx[k] = new RegExp(keys[k][0], keys[k][1]);
  const heads = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,button,summary,[role=tab],[role=button],dt,strong,b'));
  const clean = t => (t || '').replace(/\s+/g, ' ').trim();
  for (const h of heads) {
    const label = clean(h.innerText || h.textContent);
    if (!label || label.length > 60) continue;
    for (const k in rx) {
      if (out[k] || !rx[k].test(label)) continue;
      try { if (h.getAttribute('aria-expanded') === 'false') h.click(); } catch (e) {}
      let text = '';
      // 1) aria-controls, 2) nächstes Geschwister, 3) Elternelement ohne Überschrift
      const ctl = h.getAttribute('aria-controls');
      if (ctl && document.getElementById(ctl)) text = clean(document.getElementById(ctl).innerText);
      if (!text && h.nextElementSibling) text = clean(h.nextElementSibling.innerText);
      if (!text && h.parentElement) text = clean((h.parentElement.innerText || '').replace(label, ''));
      if (!text && h.parentElement && h.parentElement.nextElementSibling) text = clean(h.parentElement.nextElementSibling.innerText);
      text = text.replace(new RegExp('^' + label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '[:\\s]*', 'i'), '');
      if (text && text.length > 3 && !rx[Object.keys(rx).find(x => x !== k && rx[x].test(text.slice(0, 30)))]) out[k] = text;
    }
  }
  return out;
}
"""


def sammle_produkte(ordner):
    links = []
    for f in sorted(glob.glob(os.path.join(ordner, "*.json"))):
        name = os.path.basename(f)
        if name.startswith("_") or name == "dateien.json":
            continue
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception as e:  # defekte Datei überspringen, die Seite meldet das selbst
            print(f"! {name}: {e}", file=sys.stderr)
            continue
        for p in data if isinstance(data, list) else data.get("produkte", []):
            if p.get("link") and p.get("aktiv") is not False and p["link"] not in links:
                links.append(p["link"])
    return links


def kuerze(text, n):
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + " …"


def zusammenfassung(name_text, beschreibung):
    """Optional: kurze Zusammenfassung in eigenen Worten über die Anthropic-API."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key or not beschreibung:
        return ""
    body = {
        "model": os.environ.get("SUMMARY_MODEL", "claude-sonnet-5-5"),
        "max_tokens": 300,
        "messages": [{"role": "user", "content":
            "Fasse die folgende Produktbeschreibung in 2 bis 3 sachlichen deutschen Sätzen in eigenen Worten zusammen. "
            "Keine Heilversprechen, keine Werbesprache, nichts erfinden, was nicht im Text steht. Nur der Text, ohne Einleitung.\n\n" + beschreibung[:4000]}],
    }
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", json.dumps(body).encode(),
        {"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return "".join(b.get("text", "") for b in json.load(r).get("content", [])).strip()
    except Exception as e:
        print(f"  Zusammenfassung fehlgeschlagen: {e}", file=sys.stderr)
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--produkte", default="produkte")
    ap.add_argument("--nur-neue", action="store_true", help="Produkte, die schon Daten haben, überspringen")
    a = ap.parse_args()

    ziel = os.path.join(a.produkte, "_auto-details.json")
    alt = {}
    if os.path.exists(ziel):
        try:
            alt = json.load(open(ziel, encoding="utf-8"))
        except Exception:
            alt = {}

    links = sammle_produkte(a.produkte)
    print(f"{len(links)} Produkte gefunden")
    from playwright.sync_api import sync_playwright
    heute = datetime.date.today().isoformat()
    with sync_playwright() as p:
        kw = {}
        if os.environ.get("CHROMIUM_PATH"):
            kw["executable_path"] = os.environ["CHROMIUM_PATH"]
        browser = p.chromium.launch(**kw)
        ctx = browser.new_context(locale="de-DE", user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"))
        for link in links:
            if a.nur_neue and alt.get(link, {}).get("inhaltsstoffe"):
                continue
            print("→", link)
            seite = ctx.new_page()
            try:
                seite.goto(link, wait_until="domcontentloaded", timeout=45000)
                seite.wait_for_timeout(2500)
                for txt in ("Alle akzeptieren", "Akzeptieren", "Zustimmen"):  # Cookie-Banner wegklicken
                    try:
                        seite.get_by_role("button", name=re.compile(txt, re.I)).first.click(timeout=800)
                        break
                    except Exception:
                        pass
                gefunden = seite.evaluate(JS, {k: [v.pattern, "i"] for k, v in KEYS.items()})
            except Exception as e:
                print(f"  ! {e}", file=sys.stderr)
                seite.close()
                continue
            seite.close()
            eintrag = dict(alt.get(link, {}))
            if gefunden.get("inhaltsstoffe"):
                eintrag["inhaltsstoffe"] = kuerze(gefunden["inhaltsstoffe"], 2500)
            if gefunden.get("anwendung"):
                eintrag["anwendung"] = kuerze(gefunden["anwendung"], 900)
            if gefunden.get("beschreibung"):
                s = zusammenfassung(link, gefunden["beschreibung"])
                if s:
                    eintrag["details"] = s
            if any(eintrag.get(k) for k in ("inhaltsstoffe", "anwendung", "details")):
                eintrag["quelle"] = urlparse(link).netloc.replace("www.", "")
                eintrag["stand"] = heute
                alt[link] = eintrag
                print("  ✓", ", ".join(k for k in ("inhaltsstoffe", "anwendung", "details") if eintrag.get(k)))
            else:
                print("  – nichts gefunden")
        browser.close()
    with open(ziel, "w", encoding="utf-8") as f:
        json.dump(alt, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("gespeichert:", ziel)


if __name__ == "__main__":
    main()
