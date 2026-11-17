# Uschi's Skincare Guide

Eine interaktive Seite, die aus deiner Produktliste eine persönliche Morgen- und Abendroutine zusammenstellt. Besucher wählen Hauttyp, Themen, Erfahrung und Budget. Die Seite besteht aus einer einzigen `index.html`, die Produkte liegen als JSON-Dateien im Ordner `produkte/`.

Live: https://uschimarcel.github.io/UschisSkincare/

## Aufbau

```
index.html          Seite, Logik und Design (selten ändern)
impressum.html      Impressum
produkte/
  002-….json        Produktdateien (hier kommen neue Produkte rein)
  _vorlage.json     Vorlage mit allen Feldern (wird nicht geladen)
bilder/
  <kennung>.svg     Glas-Illustration pro Produkt (automatisch gefunden)
  _layout.json      Position der Beschriftung je Flasche (vom Skript erzeugt)
scripts/
  make_illustrations.py   erzeugt fehlende Illustrationen
ARCHIV/             Stand der Seite vor dem Redesign (wird nicht geladen)
```

Die Seite lädt alle `.json`-Dateien aus `produkte/` automatisch, sortiert nach Dateinamen (`002` vor `010`). Dateien, die mit `_` beginnen, und `dateien.json` werden ignoriert. Es ist keine Änderung an der `index.html` nötig, wenn Produkte dazukommen.

## Neue Produkte hinzufügen

1. Kopiere `_vorlage.json`, benenne die Kopie versioniert (z. B. `007-24-10-2026.json`) und fülle sie aus.
2. Lade die Datei im Ordner `produkte/` des Repositories hoch (Add file → Upload files → Commit).
3. Erzeuge die Illustration (siehe „Bilder") und lade sie in `bilder/` hoch.
4. Nach ein bis zwei Minuten und einem Neuladen ist das Produkt live.

Eine Datei ist eine Liste von Produkten:

```json
[
  {
    "link": "https://www.dm.de/p/d/…",
    "name": "Geek & Gorgeous Mighty Melt Reinigungsbalsam",
    "schritt": "Reinigungs-Öle",
    "beschreibung": "Kurzer Text zum Produkt.",
    "tags": ["trocken", "normal", "makeup"],
    "zeit": "abends",
    "preis": "12,95"
  }
]
```

## Felder

| Feld | Pflicht | Bedeutung |
|---|---|---|
| `link` | ja | Produktlink. Dient auch als eindeutige ID. |
| `name` | nein | Anzeigename. Ohne Angabe wird er aus dem Link abgeleitet. |
| `schritt` | ja | Schritt der Routine (siehe unten). |
| `beschreibung` | nein | Kurzer Text auf der Karte. |
| `tags` | nein | Hauttypen und Themen gemischt (siehe unten). |
| `bild` | nein | Eigener Bildpfad im Repository (z. B. `bilder/mein-foto.jpg`). Externe Links (`https://…`) werden bewusst ignoriert, damit keine fremden Shop-Bilder erscheinen. Ohne Angabe wird `bilder/<kennung>.svg` genutzt. |
| `zeit` | nein | `"morgens"` oder `"abends"`. Ohne Angabe: beides. |
| `erfahrung` | nein | Liste aus `anfaenger`, `erfahren`, `fortgeschritten`, `experte`. Ohne Angabe: für alle. |
| `konflikt` | nein | Schrittnamen oder Produktlinks, mit denen das Produkt nicht kombiniert werden soll. |
| `hinweis` | nein | Hellblaue Box, z. B. zur Lagerung (Kühlschrank). |
| `preis` | nein | Aktueller Preis, als Zahl oder Text (`12.95` oder `"12,95"`). |
| `preis_alt` | nein | Alter Preis. Wird durchgestrichen mit Rabatt in Prozent angezeigt. |
| `etikett` | nein | Handschrift-Beschriftung auf der Flasche (mit `SHOW_LABELS=false` in der `index.html` abschaltbar), auf der Flasche, `\n` = Zeilenumbruch (z. B. `"Mighty\nMelt"`). Ohne Angabe wird sie aus dem Namen gekürzt. |
| `farbe` | nein | Farbe der Flüssigkeit in der Illustration als Hex-Wert (z. B. `"#f0c2cc"`). Wirkt beim Erzeugen mit `make_illustrations.py`. |
| `aktiv` | nein | `false` blendet das Produkt aus. |

### Schritte (`schritt`)

Reihenfolge in der Routine:

1. **Reinigungs-Öle** (nur abends, Basis)
2. **Reinigungs-Cleanser** (morgens und abends, Basis)
3. **Peeling** (nur abends, nur bei passender Themen-Kombination)
4. **Toner**
5. **Serum** (bis zu 2, bei Thema Feuchtigkeit bis zu 3)
6. **Retinol / Anti-Aging** (nur abends)
7. **Creme** (Basis, entfällt, wenn ein feuchtigkeitsspendender Toner oder ein Serum in der Routine ist)
8. **Salbe** (nur abends, nur bei passenden Themen)
9. **Sonnenschutz** (nur morgens, Basis)

Basis-Schritte erscheinen immer. Die anderen nur, wenn ein Produkt zu den gewählten Themen passt. Gebräuchliche Schreibweisen wie `reinigung`, `cleanser`, `öl`, `retinol`, `anti-aging` oder `aha` werden erkannt.

### Tags (`tags`)

- **Hauttypen:** `trocken`, `fettig`, `mischhaut`, `empfindlich`, `normal`. Ohne Hauttyp-Tag passt das Produkt zu allen Typen. Sobald ein Typ eingetragen ist, erscheint das Produkt nur für diese Typen. Ausnahme: Bei Hauttyp „Empfindlich" sind alle Produkte im Schritt „Reinigungs-Öle" kompatibel, auch ohne dieses Tag.
- **Themen:** `akne`, `roetungen`, `falten`, `pigment`, `poren`, `feuchtigkeit`, `antiaging`, `makeup`.
- Anzeigenamen wie „Unreinheiten", „Rötungen" oder „Make-up" werden erkannt.
- Produkte im Schritt „Retinol / Anti-Aging" bekommen das Tag `antiaging` automatisch.

## So baut die Seite die Routine

- **Themen:** Mehrere sind wählbar. Pro Schritt wird das Produkt gewählt, das die meisten Themen abdeckt. „Basic" (kein Thema) zeigt die Grundroutine.
- **Make-up:** Abends erst ein Reinigungsöl, danach ein Cleanser (Double Cleansing). Ohne Make-up reicht abends das Öl, falls eines passt.
- **Peeling:** Erscheint nur, wenn alle Themen-Tags des Peeling-Produkts gewählt sind (z. B. Unreinheiten und Große Poren zusammen).
- **Anti Aging:** Fügt den Retinol-Schritt ein, unabhängig vom Hauttyp. Passt das Produkt nicht zum Hauttyp, steht oben an der Routine ein Vorsichtshinweis.
- **Erfahrung:** Die Frage erscheint nur, wenn ein Produkt mit `erfahrung` in der Routine landen würde. Produkte ohne Wert gelten für alle. Im Experten-Modus sind Warnungen und Alternativprodukte ausgeblendet.
- **Konflikte:** Stehen zwei Produkte im Konflikt, zeigt die Seite bei beiden eine Warnung, wenn möglich mit einem Alternativprodukt.
- **Budget:** Der Regler erscheint, sobald mindestens ein Produkt einen Preis hat. Liegt die Routine darüber, ersetzt die Seite Produkte durch günstigere desselben Schritts und streicht notfalls optionale Schritte. Das Menü „Aber welche sind denn nicht dabei?" zeigt, was geändert wurde.

## Produkt ausblenden oder ändern

Ein Produkt blendest du mit `"aktiv": false` aus. Spätere Dateien überschreiben frühere Einträge mit demselben `link`, Feld für Feld. Du kannst also eine neue Datei anlegen, die nur den Link und das geänderte Feld enthält, ohne die alte Datei anzufassen:

```json
[
  { "link": "https://www.dm.de/p/d/…", "aktiv": false }
]
```

## Exporte

Unter der Routine kann man sie als Bild speichern (mit Schreiblinie „Anwendung:" bei jedem Produkt, ohne Produktfotos) oder als Text kopieren.

## Fehlersuche

- **Keine Produkte sichtbar:** Meist ist eine JSON-Datei fehlerhaft (fehlendes Komma, fehlende Klammer). Hänge `?debug` an die Adresse (`…/UschisSkincare/?debug`), dann zeigt die Seite den Fehler samt Dateinamen an. Eine fehlerhafte Datei wird komplett übersprungen.
- **Änderung nicht sichtbar:** Bis zu zwei Minuten warten, dann mit Strg+F5 (Cmd+Shift+R) neu laden. Die Dateiliste wird kurz zwischengespeichert.
- **Kein Bild bei einem Produkt:** Es fehlt `bilder/<kennung>.svg`. Mit `python scripts/make_illustrations.py` erzeugen oder einen eigenen Pfad in `bild` eintragen.
- **Budget-Regler fehlt:** Kein Produkt hat einen `preis`.

## Bilder

Jedes Produkt bekommt eine realistisch gerenderte, neutrale Flasche aus mattem Glas mit Silberkappe (oder einen Tiegel bzw. eine Tube), bewusst ohne Marke oder Logo. Die Flüssigkeit hat die Produktfarbe, den Namen schreibt die Seite in fetter Marker-Schrift (Feld `etikett`) mit Unterstreichung und kleinem Schritt-Namen darauf. Die Seite sucht die Datei `bilder/<kennung>.svg`. Die Kennung ist der letzte Teil des Produktlinks in Kleinbuchstaben (z. B. `…/mivolis-panthenol-salbe` wird `bilder/mivolis-panthenol-salbe.svg`).

Neue Illustrationen erzeugst du im Repository-Ordner mit:

```
python scripts/make_illustrations.py
```

Das legt nur fehlende Dateien an (`--ueberschreiben` erneuert alle). Eigene Fotos gehen vor: Trage `"bild": "bilder/mein-foto.jpg"` beim Produkt ein. Die Bilder liegen in der Routine mit 90 % Deckkraft (normaler Modus) über der großen Zahl. Die Marker-Beschriftung auf den Flaschen ist ausgeschaltet (`SHOW_LABELS=false` in der index.html).

## Detailseiten

Ein Klick auf ein Produkt öffnet die Detailseite (`#produkt=<kennung>`) mit Anwendung, Inhaltsstoffen und Preis, sofern in der JSON hinterlegt (`anwendung`, `details`, `inhaltsstoffe`). Ein Klick neben die Seite oder Esc führt zurück zur Übersicht.

## Darkmode

Der Schalter oben rechts wechselt zwischen hell und dunkel. Ohne Auswahl folgt die Seite der Systemeinstellung.

## Hinweise

- Alle Texte sind auf Deutsch und im Du-Ton geschrieben.
- Die Seite enthält Empfehlungen und keine medizinische Beratung.
- Der Besucher-Zustand (Auswahl, Darkmode) liegt nur im Browser (localStorage).
- Es gibt keinen Passwortschutz mehr. Das Design ist brutalistisch-editorial: Haarlinien-Raster, eckige Elemente ohne Rundungen, riesige Überschrift und nummerierte Abschnitte (01/ …).

## Code

Unter der Routine erzeugt „Code erzeugen“ einen 6-stelligen Code mit der Auswahl (Hauttyp, Themen, Erfahrung, Budget). Die Seite zeigt nur Platzhalter-Illustrationen, ein Hinweis erklärt warum.
